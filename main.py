from __future__ import annotations

# Конфиг Kivy надо ставить ДО импорта kivy, иначе не сработает!
import os
import sys

def _is_android() -> bool:
    """Проверка - запущено на телефоне или на компе"""
    return 'ANDROID_ARGUMENT' in os.environ or 'ANDROID_PRIVATE' in os.environ

# Настройки для Android - без них приложение вылетает
if _is_android():
    # Выключаем аппаратное ускорение - с ним на некоторых телефонах краш
    os.environ.setdefault('SDL_RENDER_DRIVER', 'software')
    os.environ.setdefault('KIVY_GL_BACKEND', 'gl')
    os.environ.setdefault('SDL_RENDER_BATCHING', '0')
    os.environ.setdefault('SDL_HINT_RENDER_DRIVER', 'software')
else:
    # На компе всё проще
    os.environ.setdefault('KIVY_GL_BACKEND', 'gl')

# Настройки Kivy
from kivy.config import Config
Config.set('graphics', 'multisamples', '0')  # без этого на андроиде глючит
if _is_android():
    Config.set('kivy', 'pause_on_minimize', '0')

import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, DictProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, SlideTransition

from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.dialog.dialog import (
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
)
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.snackbar import MDSnackbar

# Наши экраны
from screens.home_screen import HomeScreen
from screens.courses_screen import CoursesScreen
from screens.course_topic_screen import CourseTopicScreen
from screens.theory_screen import TheoryScreen
from screens.quiz_screen import QuizScreen
from screens.molecules_screen import MoleculesScreen
from screens.molecule_viewer_screen import MoleculeViewerScreen
from screens.molecule_editor_screen import MoleculeEditorScreen
from screens.reaction_viewer_screen import ReactionViewerScreen
from screens.reactions_screen import ReactionsScreen
from screens.reaction_editor_screen import ReactionEditorScreen
from screens.ai_assistant_screen import AIAssistantScreen
from screens.model_download_screen import ModelDownloadScreen

from utils.ai_engine import AIEngine
from utils.course_repo import CourseRepo
from utils.model_bootstrap import ensure_gguf_ready, needs_download
from theme import THEME


# Пути к файлам проекта
PROJECT_DIR = Path(__file__).resolve().parent

KV_PATH = PROJECT_DIR / "kv" / "main.kv"
COURSES_DB = PROJECT_DIR / "data" / "courses" / "courses.db"
HF_TOKEN = PROJECT_DIR / "data" / "secrets" / "hf_token.txt"

# Модель для оффлайн ИИ (файл разбит на части в assets/models/)
OFFLINE_MODEL_NAME = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"

MOLECULES_DIR = PROJECT_DIR / "assets" / "molecules"
REACTIONS_DIR = PROJECT_DIR / "assets" / "reactions"


def _db_conn(db_path: str) -> sqlite3.Connection:
    """Подключаемся к базе данных"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # чтобы можно было обращаться по имени столбца
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def ensure_mm_tables(db_path: str) -> None:
    """Создаём таблицы для тестов, если их ещё нет"""
    with _db_conn(db_path) as conn:
        cur = conn.cursor()

        # Таблица с тестами
        cur.execute("""
        CREATE TABLE IF NOT EXISTS mm_quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            section_id INTEGER,
            topic_id INTEGER,
            title TEXT NOT NULL,
            created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
            FOREIGN KEY(section_id) REFERENCES course_sections(id) ON DELETE SET NULL,
            FOREIGN KEY(topic_id) REFERENCES course_topics(id) ON DELETE SET NULL
        );
        """)

        # Вопросы к тестам
        cur.execute("""
        CREATE TABLE IF NOT EXISTS mm_quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            q TEXT NOT NULL,
            options_json TEXT NOT NULL,
            correct_index INTEGER NOT NULL,
            explanation TEXT,
            order_index INTEGER NOT NULL,
            FOREIGN KEY(quiz_id) REFERENCES mm_quizzes(id) ON DELETE CASCADE
        );
        """)

        # Попытки прохождения тестов
        cur.execute("""
        CREATE TABLE IF NOT EXISTS mm_quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            started_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            finished_at TEXT,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percent REAL NOT NULL,
            FOREIGN KEY(quiz_id) REFERENCES mm_quizzes(id) ON DELETE CASCADE
        );
        """)

        # Прогресс по курсам
        cur.execute("""
        CREATE TABLE IF NOT EXISTS mm_course_progress (
            course_id INTEGER PRIMARY KEY,
            best_percent REAL NOT NULL DEFAULT 0,
            last_percent REAL NOT NULL DEFAULT 0,
            attempts_count INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
        );
        """)

        conn.commit()


def seed_quizzes_if_needed(db_path: str) -> bool:
    """Заполняем базу вопросами, если она пустая"""
    with _db_conn(db_path) as conn:
        cur = conn.cursor()
        q_count = int(cur.execute("select count(*) from mm_quiz_questions").fetchone()[0])
        if q_count > 0:
            return False  # вопросы уже есть

        courses = cur.execute("select id, title from courses order by id").fetchall()
        if not courses:
            return False

        # Базовые вопросы по химии для теста
        base_questions = [
            (
                "Какая связь образуется при боковом перекрытии p-орбиталей?",
                ["Сигма-связь", "Пи-связь", "Ионная связь", "Водородная связь"],
                1,
                "Пи-связь образуется при боковом перекрытии p-орбиталей.",
            ),
            (
                "Алканы относятся к:",
                ["Ненасыщенным углеводородам", "Насыщенным углеводородам", "Кислородсодержащим соединениям", "Азотсодержащим соединениям"],
                1,
                "Алканы содержат только одинарные связи и являются насыщенными.",
            ),
            (
                "Изомерия — это:",
                ["Разный состав", "Одинаковый состав и разное строение", "Одинаковое строение и разная масса", "Только разное агрегатное состояние"],
                1,
                "Изомеры имеют одинаковую формулу, но различаются строением или пространственным расположением.",
            ),
            (
                "Фенолы дают характерную окраску с:",
                ["FeCl3", "NaHCO3", "AgNO3", "KMnO4"],
                0,
                "Фенолы образуют окрашенные комплексы с FeCl3.",
            ),
            (
                "Карбоновые кислоты с карбонатами выделяют газ:",
                ["H2", "CO2", "NH3", "Cl2"],
                1,
                "Кислота + карбонат -> CO2 + соль + вода.",
            ),
            (
                "Степень окисления — это:",
                ["Число связей атома", "Условный заряд атома в соединении", "Реальный заряд иона", "Число нейтронов"],
                1,
                "Степень окисления — условный заряд при допущении ионного характера связей.",
            ),
            (
                "Принцип Ле Шателье описывает:",
                ["Скорость реакции", "Смещение равновесия при изменении условий", "Растворимость", "Только каталитические реакции"],
                1,
                "При внешнем воздействии равновесие смещается в сторону ослабления воздействия.",
            ),
            (
                "Катализатор в реакции:",
                ["Смещает равновесие", "Уменьшает энергию активации", "Всегда расходуется полностью", "Делает реакцию эндотермической"],
                1,
                "Катализатор снижает энергию активации и ускоряет реакцию, не смещая равновесие.",
            ),
        ]

        # Добавляем тест для каждого курса
        for course in courses:
            course_id = int(course["id"])
            title = str(course["title"])
            quiz_title = f"Итоговый тест: {title}"

            cur.execute("insert into mm_quizzes(course_id, title) values (?, ?)", (course_id, quiz_title))
            quiz_id = int(cur.lastrowid)

            for idx, (q, opts, correct, expl) in enumerate(base_questions, start=1):
                cur.execute(
                    "insert into mm_quiz_questions(quiz_id, q, options_json, correct_index, explanation, order_index) "
                    "values (?, ?, ?, ?, ?, ?)",
                    (quiz_id, q, json.dumps(opts, ensure_ascii=False), int(correct), expl, idx),
                )

        conn.commit()
        return True


class MoleculeMentorApp(MDApp):
    """Главный класс приложения"""
    
    top_title = StringProperty("Molecule Mentor")
    back_visible = BooleanProperty(False)
    ai_status = StringProperty("N/A")
    nav_state = DictProperty({})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Пути к ресурсам
        self.project_dir = str(PROJECT_DIR)
        self.courses_db = str(COURSES_DB)
        self.molecules_dir = str(MOLECULES_DIR)
        self.reactions_dir = str(REACTIONS_DIR)

        # Цвета из темы (используются в kv файлах)
        self.mm_bg = THEME.bg
        self.mm_surface = THEME.surface
        self.mm_surface2 = THEME.surface2
        self.mm_primary = THEME.primary
        self.mm_accent = THEME.accent
        self.mm_button_color = THEME.button_color
        self.mm_text = THEME.text
        self.mm_text2 = THEME.text2

        # Цвета для карточек молекул
        self.mm_molecules_card_bg = self.mm_surface2
        self.mm_molecules_card_border = (1, 1, 1, 0.16)
        self.mm_molecules_card_pressed_delta = 0.08
        self.mm_molecules_card_elevation = 2
        self.mm_molecules_list_spacing = 4
        self.mm_molecules_list_bottom_padding = 8

        # Пул потоков для фоновых задач (чтобы UI не тормозил)
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mm")
        self._ai_engine: Optional[AIEngine] = None
        self._ai_dialog: Optional[MDDialog] = None
        self._ai_lock = threading.RLock()

        # Проверяем базу данных
        if not COURSES_DB.exists():
            raise FileNotFoundError(f"База курсов не найдена: {COURSES_DB}")

        ensure_mm_tables(self.courses_db)
        self.course_repo = CourseRepo(self.courses_db)
        self._nav_stack: list[str] = ["home"]  # стек навигации для кнопки "назад"

    def build(self):
        """Строим интерфейс приложения"""
        self.theme_cls.material_style = "M3"
        if not KV_PATH.exists():
            raise FileNotFoundError(f"KV файл не найден: {KV_PATH}")

        root = Builder.load_file(str(KV_PATH))
        sm: ScreenManager = root.ids.sm

        # Добавляем все экраны
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(CoursesScreen(name="courses"))
        sm.add_widget(CourseTopicScreen(name="course_topic"))
        sm.add_widget(TheoryScreen(name="theory"))
        sm.add_widget(QuizScreen(name="quiz"))
        sm.add_widget(MoleculesScreen(name="molecules"))
        sm.add_widget(MoleculeViewerScreen(name="molecule_viewer"))
        sm.add_widget(MoleculeEditorScreen(name="molecule_editor"))
        sm.add_widget(ReactionsScreen(name="reactions"))
        sm.add_widget(ReactionViewerScreen(name="reaction_viewer"))
        sm.add_widget(ReactionEditorScreen(name="reaction_editor"))
        sm.add_widget(AIAssistantScreen(name="ai_assistant"))
        sm.add_widget(ModelDownloadScreen(name="model_download"))

        sm.current = "home"
        return root

    def on_start(self):
        """Запускается при старте приложения"""
        # Создаём папку для данных пользователя
        try:
            Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print("[WARN] не удалось создать папку данных:", e)

        # Путь к модели ИИ
        offline_target = str(Path(self.user_data_dir).resolve() / "models" / OFFLINE_MODEL_NAME)

        self._ai_engine = AIEngine(
            hf_token_path=str(HF_TOKEN),
            offline_model_path=offline_target,
        )

        # Проверяем, нужно ли скачать модель (для Lite версии без модели)
        need_dl = needs_download(OFFLINE_MODEL_NAME)
        print(f"[STARTUP] нужна загрузка модели: {need_dl}")
        if need_dl:
            print("[STARTUP] показываем экран загрузки")
            self._show_download_screen_on_start()
        else:
            print("[STARTUP] готовим модель в фоне")
            self._prepare_offline_model_async()

        # Обновляем статус ИИ каждые 15 секунд
        Clock.schedule_interval(lambda *_: self._refresh_ai_status_async(), 15.0)
        self._refresh_ai_status_async()

        # Заполняем тесты в фоне
        self._executor.submit(self._seed_quizzes_background)

        self.set_top_title("Главная")
        self.set_back_visible(False)
    
    def _show_download_screen_on_start(self):
        """Показывает экран загрузки при первом запуске"""
        def show_screen(dt):
            self.open_model_download()
        Clock.schedule_once(show_screen, 0.5)

    def _prepare_offline_model_async(self) -> None:
        """Собираем модель из частей в фоновом потоке"""
        def work():
            try:
                print("[OFFLINE] собираю модель...")
                p = ensure_gguf_ready(OFFLINE_MODEL_NAME)
                print(f"[OFFLINE] модель готова: {p}")
                if self._ai_engine:
                    self._ai_engine.set_offline_model_path(str(p))

                def notify(_dt):
                    self.toast("Оффлайн модель готова")
                    self._refresh_ai_status_async()

                Clock.schedule_once(notify, 0)
            except Exception as e:
                import traceback
                print(f"[OFFLINE] ошибка: {e}")
                traceback.print_exc()
                
                def notify_err(_dt):
                    self.toast(f"Оффлайн модель недоступна: {e}")
                    self._refresh_ai_status_async()

                Clock.schedule_once(notify_err, 0)

        self._executor.submit(work)

    def on_stop(self):
        """При закрытии приложения"""
        try:
            if self._ai_engine:
                self._ai_engine.stop()
        except Exception:
            pass
        try:
            self._executor.shutdown(wait=True, cancel_futures=True)
        except Exception:
            pass

    def toast(self, text: str) -> None:
        """Показываем всплывающее сообщение"""
        try:
            MDSnackbar(text=text, y=24).open()
        except Exception:
            print("[MSG]", text)

    def _sm(self) -> ScreenManager:
        """Получаем менеджер экранов"""
        return self.root.ids.sm

    def set_top_title(self, title: str) -> None:
        """Устанавливаем заголовок в шапке"""
        self.top_title = title

    def set_back_visible(self, visible: bool) -> None:
        """Показать/скрыть кнопку назад"""
        self.back_visible = bool(visible)

    def _set_screen(self, name: str, push: bool = True, force: bool = False) -> None:
        """Переключаемся на другой экран"""
        sm = self._sm()

        # Если уже на этом экране
        if sm.current == name:
            if force:
                try:
                    scr = sm.get_screen(name)
                    if hasattr(scr, "refresh"):
                        scr.refresh()
                    else:
                        scr.dispatch("on_pre_enter")
                except Exception:
                    pass
            return

        sm.transition = SlideTransition(direction="left")
        sm.current = name

        # Запоминаем в стек для кнопки "назад"
        if push and (not self._nav_stack or self._nav_stack[-1] != name):
            self._nav_stack.append(name)

        self.set_back_visible(name != "home")

    def go_back(self) -> None:
        """Возврат на предыдущий экран"""
        if len(self._nav_stack) <= 1:
            self.open_home()
            return
        
        current = self._nav_stack.pop()
        prev = self._nav_stack[-1]
        
        # Чистим состояние навигации
        st = dict(self.nav_state or {})
        if current == "theory":
            st.pop("topic_id", None)
            st.pop("topic_title", None)
        elif current == "course_topic" and st.get("section_id"):
            st.pop("section_id", None)
            st.pop("section_title", None)
        self.nav_state = st
        
        sm = self._sm()
        sm.transition = SlideTransition(direction="right")
        sm.current = prev
        
        # Обновляем экран
        try:
            scr = sm.get_screen(prev)
            if hasattr(scr, "on_pre_enter"):
                scr.dispatch("on_pre_enter")
        except Exception:
            pass
        
        self.set_back_visible(prev != "home")

    # ====== Методы навигации ======
    
    def open_home(self) -> None:
        """На главную"""
        self.nav_state = {}
        self._nav_stack = ["home"]
        self.set_top_title("Главная")
        self._set_screen("home", push=False)

    def open_courses(self) -> None:
        """Открыть курсы"""
        self.nav_state = {}
        self.set_top_title("Курсы")
        self._set_screen("courses")

    def open_molecules(self) -> None:
        """Открыть библиотеку молекул"""
        self.nav_state = {}
        self.set_top_title("Молекулы")
        self._set_screen("molecules")

    def open_molecule_viewer(self, pdb_path: str, title: str, description: str = "") -> None:
        """Открыть 3D просмотр молекулы"""
        self.nav_state = {"pdb_path": pdb_path, "title": title, "description": description}
        self.set_top_title(title)
        self._set_screen("molecule_viewer")

    def open_molecule_editor(self, pdb_path: str, title: str) -> None:
        """Открыть редактор молекулы"""
        self.nav_state = {"pdb_path": pdb_path, "title": title}
        self.set_top_title(title)
        self._set_screen("molecule_editor")

    def open_reactions(self) -> None:
        """Открыть библиотеку реакций"""
        self.nav_state = {}
        self.set_top_title("Реакции")
        self._set_screen("reactions")
        
    def open_reaction_viewer(self, reaction_id: str, title: str) -> None:
        """Открыть просмотр реакции"""
        self.nav_state = {"reaction_id": str(reaction_id), "title": str(title)}
        self.set_top_title(title)
        self._set_screen("reaction_viewer")
    
    def open_reaction_editor(self) -> None:
        """Открыть редактор реакций"""
        self.nav_state = {}
        self.set_top_title("Похимичим!")
        self._set_screen("reaction_editor")

    def open_ai_assistant(self) -> None:
        """Открыть чат с ИИ"""
        self.set_top_title("ИИ-помощник")
        self._set_screen("ai_assistant")
    
    def open_model_download(self) -> None:
        """Открыть экран загрузки модели"""
        self.set_top_title("Загрузка модели")
        self._set_screen("model_download")
        
    def open_course(self, course_id: int, course_title: str) -> None:
        """Открыть курс (список разделов)"""
        st = dict(self.nav_state or {})
        st["course_id"] = int(course_id)
        st["course_title"] = str(course_title)
        st.pop("section_id", None)
        st.pop("section_title", None)
        st.pop("topic_id", None)
        st.pop("topic_title", None)
        self.nav_state = st
        self.set_top_title(course_title)
        self._set_screen("course_topic")

    def open_section(self, section_id: int, section_title: str) -> None:
        """Открыть раздел курса (список тем)"""
        st = dict(self.nav_state or {})
        st["section_id"] = int(section_id)
        st["section_title"] = str(section_title)
        st.pop("topic_id", None)
        st.pop("topic_title", None)
        self.nav_state = st
        self.set_top_title(section_title)
        self._set_screen("course_topic", force=True)

    def open_topic(self, topic_id: int, topic_title: str) -> None:
        """Открыть тему (теория)"""
        st = dict(self.nav_state or {})
        st["topic_id"] = int(topic_id)
        st["topic_title"] = str(topic_title)
        self.nav_state = st
        self.set_top_title(topic_title)
        self._set_screen("theory")

    def open_quiz_for_course(self, course_id: int) -> None:
        """Открыть тест по курсу"""
        self.nav_state = {"course_id": int(course_id)}
        self.set_top_title("Тест")
        self._set_screen("quiz")

    # ====== ИИ ======
    
    def _refresh_ai_status_async(self) -> None:
        """Обновляем статус ИИ"""
        if not self._ai_engine:
            self.ai_status = "N/A"
            return

        fut = self._executor.submit(self._ai_engine.diagnose)

        def on_done(_dt):
            try:
                d = fut.result()
                mode = str(getattr(d, "mode", "N/A"))
                if mode == "N/A" and not getattr(d, "online_reachable", True):
                    mode = "OFFLINE"
                self.ai_status = mode
            except Exception:
                self.ai_status = "N/A"

        Clock.schedule_once(on_done, 0)

    def show_ai_info(self) -> None:
        """Показываем информацию о состоянии ИИ"""
        if not self._ai_engine:
            self.toast("ИИ ещё не готов")
            return

        fut = self._executor.submit(self._ai_engine.diagnose)

        def on_done(_dt):
            try:
                d = fut.result()
                data = asdict(d)

                lines = [
                    f"Статус: {data.get('mode')}",
                    f"Онлайн-доступен: {'Да' if data.get('online_reachable') else 'Нет'}",
                    f"HF токен: {'OK' if data.get('hf_token_exists') else 'Нет'}",
                    f"Оффлайн-модель готова: {'Да' if data.get('offline_model_exists') else 'Нет'}",
                    f"llama_cpp: {'OK' if data.get('llama_import_ok') else 'Нет'}",
                ]
                if data.get("online_last_error"):
                    lines.append(f"Ошибка online: {str(data.get('online_last_error'))[:120]}")
                if data.get("llama_last_error"):
                    lines.append(f"Ошибка offline: {str(data.get('llama_last_error'))[:120]}")

                msg = "\n".join(lines)
            except Exception as e:
                msg = f"Ошибка диагностики: {e}"

            if self._ai_dialog:
                try:
                    self._ai_dialog.dismiss()
                except Exception:
                    pass

            self._ai_dialog = MDDialog(
                MDDialogHeadlineText(text="ИИ: диагностика"),
                MDDialogSupportingText(text=msg),
                MDDialogButtonContainer(
                    MDButton(
                        MDButtonText(text="OK"),
                        style="text",
                        on_release=lambda *_: self._ai_dialog.dismiss() if self._ai_dialog else None,
                    ),
                ),
            )
            self._ai_dialog.open()

        Clock.schedule_once(on_done, 0)

    def _seed_quizzes_background(self) -> None:
        """Заполняем тесты в фоне"""
        try:
            seeded = seed_quizzes_if_needed(self.courses_db)

            def notify(_dt):
                self.toast("Тесты подготовлены" if seeded else "Тесты уже готовы")

            Clock.schedule_once(notify, 0)
        except Exception as e:
            def notify_err(_dt):
                self.toast(f"Ошибка подготовки тестов: {e}")
            Clock.schedule_once(notify_err, 0)


if __name__ == "__main__":
    MoleculeMentorApp().run()
