from __future__ import annotations

"""
Экран прохождения викторины.
"""

import json
import random
import sqlite3
import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.progressindicator import MDLinearProgressIndicator
from kivymd.uix.scrollview import MDScrollView

from .base_screen import BaseScreen


@dataclass(frozen=True)
class Question:
    """Вопрос викторины."""
    text: str
    options: List[str]
    correct: int
    explanation: str
    difficulty: int = 1


class OptionRow(ButtonBehavior, BoxLayout):
    """Кликабельная строка с вариантом ответа."""

    def __init__(self, text: str, index: int, selected: bool = False, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(52)
        self.padding = [dp(14), dp(6), dp(14), dp(6)]
        self.spacing = dp(10)

        self._selected = selected
        self._on_select = on_select
        self._text = text
        self._index = index
        self._review_state: Optional[str] = None
        self._disabled = False


        self._letters = ["А", "Б", "В", "Г", "Д", "Е"]


        self._bg_normal = (0.12, 0.14, 0.22, 1)
        self._bg_selected = (0.2, 0.35, 0.55, 1)
        self._bg_correct = (0.15, 0.5, 0.25, 1)
        self._bg_wrong = (0.55, 0.15, 0.15, 1)
        self._bg_missed = (0.2, 0.45, 0.3, 1)

        with self.canvas.before:
            Color(*self._bg_normal)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])

        self.bind(pos=self._update_rect, size=self._update_rect)


        letter = self._letters[index] if index < len(self._letters) else str(index + 1)
        self._letter_label = MDLabel(
            text=letter,
            bold=True,
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=(0.7, 0.75, 0.85, 1),
            font_size=sp(15),
            size_hint=(None, None),
            size=(dp(28), dp(28)),
        )


        self._text_label = MDLabel(
            text=text,
            halign="left",
            valign="middle",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_size=sp(14),
        )

        self.add_widget(self._letter_label)
        self.add_widget(self._text_label)

        self._update_visuals()

    def _update_rect(self, *_):
        if hasattr(self, '_bg_rect'):
            self._bg_rect.pos = self.pos
            self._bg_rect.size = self.size

    def _update_visuals(self):
        """Обновляем цвет фона."""
        self.canvas.before.clear()
        with self.canvas.before:
            if self._review_state == "correct":
                Color(*self._bg_correct)
            elif self._review_state == "wrong":
                Color(*self._bg_wrong)
            elif self._review_state == "missed":
                Color(*self._bg_missed)
            elif self._selected:
                Color(*self._bg_selected)
            else:
                Color(*self._bg_normal)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])


        if self._selected or self._review_state:
            self._letter_label.text_color = (1, 1, 1, 1)
        else:
            self._letter_label.text_color = (0.7, 0.75, 0.85, 1)

    def set_selected(self, selected: bool):
        if self._selected != selected:
            self._selected = selected
            self._update_visuals()

    def set_review_state(self, state: Optional[str]):
        """Устанавливает состояние проверки: 'correct', 'wrong', 'missed' или None."""
        self._review_state = state
        self._update_visuals()

    def set_clickable(self, clickable: bool):
        """Включает/отключает возможность выбора."""
        self._disabled = not clickable

    def on_release(self):
        if self._on_select and not self._disabled:
            self._on_select(self._index)


class QuizScreen(BaseScreen):
    """Экран викторины или теста."""

    def on_pre_enter(self, *args):
        app = self.get_app()
        if app.nav_state.get("quiz_category"):
            self.title = str(app.nav_state.get("quiz_title", "Викторина"))
        else:
            self.title = "Тест"
        super().on_pre_enter(*args)
        Clock.schedule_once(lambda *_: self._load(), 0)

    def _conn(self) -> sqlite3.Connection:
        app = self.get_app()
        conn = sqlite3.connect(app.courses_db)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _load(self):
        """Загружает вопросы и строит интерфейс."""
        app = self.get_app()
        self.clear_widgets()


        category = app.nav_state.get("quiz_category")
        section_id = app.nav_state.get("section_id")
        course_id = app.nav_state.get("course_id")

        if category:
            self._load_category_quiz(category)
        elif section_id:
            self._load_section_quiz(section_id)
        elif course_id:
            self._load_course_quiz(course_id)
        else:
            self._show_error("Не выбрана викторина")

    def _load_category_quiz(self, category: str):
        """Загружает викторину по категории."""
        try:
            from data.quiz_questions import get_questions_by_category

            raw_questions = get_questions_by_category(category)
            if not raw_questions:
                self._show_error(f"Нет вопросов для категории: {category}")
                return


            random.shuffle(raw_questions)


            app = self.get_app()
            max_count = app.nav_state.get("quiz_count", 10)
            raw_questions = raw_questions[:max_count]


            self._questions: List[Question] = []
            for q in raw_questions:

                options = list(q["options"])
                correct_text = options[q["correct"]]
                random.shuffle(options)
                new_correct = options.index(correct_text)

                self._questions.append(Question(
                    text=q["q"],
                    options=options,
                    correct=new_correct,
                    explanation=q.get("explanation", ""),
                    difficulty=q.get("difficulty", 1),
                ))

            title = app.nav_state.get("quiz_title", "Викторина")
            self._quiz_title = title
            self._quiz_id = None
            self._course_id = None

            self._build_quiz_ui()

        except ImportError as e:
            self._show_error(f"Ошибка загрузки вопросов: {e}")

    def _load_section_quiz(self, section_id: int):
        """Загружает тест по разделу курса."""
        app = self.get_app()
        section_title = app.nav_state.get("section_title", "Раздел")

        with self._conn() as c:

            quiz = c.execute(
                "select id, title from mm_quizzes where section_id=? limit 1",
                (int(section_id),),
            ).fetchone()

            if not quiz:

                self._load_section_quiz_from_file(section_id, section_title)
                return

            quiz_id = int(quiz["id"])
            q_rows = c.execute(
                "select q, options_json, correct_index, explanation from mm_quiz_questions where quiz_id=? order by order_index",
                (quiz_id,),
            ).fetchall()

        self._quiz_id = quiz_id
        self._course_id = None
        self._quiz_title = str(quiz["title"])

        self._questions: List[Question] = []
        for r in q_rows:
            opts = json.loads(r["options_json"])

            correct_text = opts[int(r["correct_index"])]
            random.shuffle(opts)
            new_correct = opts.index(correct_text)

            self._questions.append(Question(
                text=str(r["q"]),
                options=[str(x) for x in opts],
                correct=new_correct,
                explanation=str(r["explanation"] or ""),
            ))

        if not self._questions:
            self._show_error("В тесте нет вопросов.")
            return


        random.shuffle(self._questions)

        self._build_quiz_ui()

    def _load_section_quiz_from_file(self, section_id: int, section_title: str):
        """Загружает тест раздела из файла quiz_questions.py (если нет в БД)."""
        try:
            from data.quiz_questions import get_questions_by_section

            raw_questions = get_questions_by_section(section_id)
            if not raw_questions:
                self._show_error(f"Нет вопросов для раздела: {section_title}")
                return


            random.shuffle(raw_questions)


            self._questions: List[Question] = []
            for q in raw_questions:

                options = list(q["options"])
                correct_text = options[q["correct"]]
                random.shuffle(options)
                new_correct = options.index(correct_text)

                self._questions.append(Question(
                    text=q["q"],
                    options=options,
                    correct=new_correct,
                    explanation=q.get("explanation", ""),
                    difficulty=q.get("difficulty", 1),
                ))

            self._quiz_title = f"Тест: {section_title}"
            self._quiz_id = None
            self._course_id = None

            self._build_quiz_ui()

        except ImportError as e:
            self._show_error(f"Ошибка загрузки вопросов: {e}")

    def _load_course_quiz(self, course_id: int):
        """Загружает тест по курсу (итоговый тест курса, без привязки к разделу)."""
        with self._conn() as c:

            quiz = c.execute(
                """SELECT id, title FROM mm_quizzes
                   WHERE course_id=? AND section_id IS NULL AND id > 0
                   ORDER BY id LIMIT 1""",
                (int(course_id),),
            ).fetchone()

            if not quiz:
                self._show_error("Итоговый тест курса не найден.")
                return

            quiz_id = int(quiz["id"])
            q_rows = c.execute(
                "select q, options_json, correct_index, explanation from mm_quiz_questions where quiz_id=? order by order_index",
                (quiz_id,),
            ).fetchall()

        self._quiz_id = quiz_id
        self._course_id = int(course_id)
        self._quiz_title = str(quiz["title"])

        self._questions: List[Question] = []
        for r in q_rows:
            opts = json.loads(r["options_json"])
            self._questions.append(Question(
                text=str(r["q"]),
                options=[str(x) for x in opts],
                correct=int(r["correct_index"]),
                explanation=str(r["explanation"] or ""),
            ))

        if not self._questions:
            self._show_error("В тесте нет вопросов.")
            return

        self._build_quiz_ui()

    def _show_error(self, message: str):
        """Показывает сообщение об ошибке."""
        app = self.get_app()
        root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(16))

        root.add_widget(Widget(size_hint_y=0.3))

        error_label = MDLabel(
            text=message,
            halign="center",
            theme_text_color="Custom",
            text_color=app.mm_text,
            font_size=sp(16),
        )
        root.add_widget(error_label)

        back_btn = MDButton(
            style="filled",
            size_hint=(None, None),
            size=(dp(150), dp(44)),
            pos_hint={"center_x": 0.5},
            md_bg_color=app.mm_primary,
            on_release=lambda *_: app.go_back(),
        )
        back_btn.add_widget(MDButtonText(text="Назад"))
        root.add_widget(back_btn)

        root.add_widget(Widget(size_hint_y=0.5))

        self.add_widget(root)

    def _build_quiz_ui(self):
        """Строит интерфейс викторины."""
        app = self.get_app()

        self._current_index = 0
        self._answers: Dict[int, int] = {}
        self._submitted = False
        self._start_time = time.time()

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))


        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(70), spacing=dp(6))


        title_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28))
        title_label = MDLabel(
            text=self._quiz_title,
            bold=True,
            halign="left",
            theme_text_color="Custom",
            text_color=app.mm_text,
            font_size=sp(16),
        )
        title_row.add_widget(title_label)


        self._counter_label = MDLabel(
            text=f"1/{len(self._questions)}",
            halign="right",
            theme_text_color="Custom",
            text_color=app.mm_accent,
            font_size=sp(14),
            size_hint_x=None,
            width=dp(60),
        )
        title_row.add_widget(self._counter_label)
        header.add_widget(title_row)


        self._progress = MDLinearProgressIndicator(
            value=0,
            size_hint_y=None,
            height=dp(6),
        )
        header.add_widget(self._progress)

        root.add_widget(header)


        self._question_container = BoxLayout(orientation="vertical")
        root.add_widget(self._question_container)


        nav_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(50), spacing=dp(12))

        self._prev_btn = MDButton(
            style="outlined",
            size_hint_x=0.3,
            on_release=lambda *_: self._prev_question(),
        )
        self._prev_btn.add_widget(MDButtonText(text="Назад"))
        nav_row.add_widget(self._prev_btn)

        self._next_btn = MDButton(
            style="filled",
            size_hint_x=0.7,
            md_bg_color=app.mm_primary,
            on_release=lambda *_: self._next_question(),
        )
        self._next_btn_text = MDButtonText(text="Далее")
        self._next_btn.add_widget(self._next_btn_text)
        nav_row.add_widget(self._next_btn)

        root.add_widget(nav_row)

        self.add_widget(root)


        self._show_question(0)

    def _show_question(self, index: int):
        """Показывает вопрос по индексу."""
        if index < 0 or index >= len(self._questions):
            return

        self._current_index = index
        q = self._questions[index]
        app = self.get_app()


        self._counter_label.text = f"{index + 1}/{len(self._questions)}"
        self._progress.value = (index + 1) / len(self._questions)


        self._prev_btn.disabled = (index == 0)
        self._prev_btn.opacity = 0.5 if index == 0 else 1

        is_last = (index == len(self._questions) - 1)
        self._next_btn_text.text = "Завершить" if is_last else "Далее"


        self._question_container.clear_widgets()


        question_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=[dp(12), dp(16)],
        )
        question_box.bind(minimum_height=question_box.setter('height'))


        difficulty_text = ["Легко", "Средне", "Сложно"][min(q.difficulty - 1, 2)]
        difficulty_color = [(0.3, 0.8, 0.4, 1), (0.9, 0.7, 0.2, 1), (0.9, 0.35, 0.3, 1)][min(q.difficulty - 1, 2)]

        diff_label = MDLabel(
            text=difficulty_text,
            halign="left",
            theme_text_color="Custom",
            text_color=difficulty_color,
            font_size=sp(11),
            size_hint_y=None,
            height=dp(18),
        )
        question_box.add_widget(diff_label)

        q_label = MDLabel(
            text=q.text,
            halign="left",
            theme_text_color="Custom",
            text_color=app.mm_text,
            font_size=sp(16),
            size_hint_y=None,
        )
        q_label.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1] + dp(10)))
        question_box.add_widget(q_label)

        self._question_container.add_widget(question_box)


        scroll = MDScrollView(size_hint_y=1)
        options_box = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            padding=[0, dp(8)],
        )
        options_box.bind(minimum_height=options_box.setter('height'))

        self._option_rows: List[OptionRow] = []
        selected = self._answers.get(index)

        for i, opt in enumerate(q.options):
            row = OptionRow(
                text=opt,
                index=i,
                selected=(selected == i),
                on_select=lambda idx: self._on_option_select(idx),
            )
            self._option_rows.append(row)
            options_box.add_widget(row)

        scroll.add_widget(options_box)
        self._question_container.add_widget(scroll)

    def _on_option_select(self, option_index: int):
        """Обработчик выбора варианта."""
        if self._submitted:
            return

        self._answers[self._current_index] = option_index


        for i, row in enumerate(self._option_rows):
            row.set_selected(i == option_index)

    def _prev_question(self):
        """Переход к предыдущему вопросу."""
        if self._current_index > 0:
            self._show_question(self._current_index - 1)

    def _next_question(self):
        """Переход к следующему вопросу или завершение."""

        if self._current_index not in self._answers:
            self.get_app().toast("Выберите ответ")
            return

        if self._current_index < len(self._questions) - 1:
            self._show_question(self._current_index + 1)
        else:
            self._submit()

    def _submit(self):
        """Завершение викторины и показ результатов."""
        if len(self._answers) < len(self._questions):

            for i in range(len(self._questions)):
                if i not in self._answers:
                    self._show_question(i)
                    self.get_app().toast(f"Ответьте на вопрос {i + 1}")
                    return

        self._submitted = True
        elapsed = time.time() - self._start_time


        score = 0
        for idx, q in enumerate(self._questions):
            if self._answers.get(idx) == q.correct:
                score += 1

        total = len(self._questions)
        percent = round(score * 100.0 / total, 1)


        self._save_result(score, total, percent)


        self._show_results(score, total, percent, elapsed)

    def _save_result(self, score: int, total: int, percent: float):
        """Сохраняет результат в базу данных."""
        try:
            with self._conn() as c:

                quiz_id = self._quiz_id if self._quiz_id else 0

                c.execute(
                    "insert into mm_quiz_attempts(quiz_id, finished_at, score, total, percent) "
                    "values (?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?, ?, ?)",
                    (quiz_id, score, total, percent),
                )

                if self._course_id:
                    row = c.execute(
                        "select best_percent, attempts_count from mm_course_progress where course_id=?",
                        (self._course_id,),
                    ).fetchone()

                    if row:
                        best = max(float(row["best_percent"]), percent)
                        attempts = int(row["attempts_count"]) + 1
                        c.execute(
                            "update mm_course_progress set best_percent=?, last_percent=?, attempts_count=?, "
                            "updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') where course_id=?",
                            (best, percent, attempts, self._course_id),
                        )
                    else:
                        c.execute(
                            "insert into mm_course_progress(course_id, best_percent, last_percent, attempts_count) "
                            "values (?, ?, ?, ?)",
                            (self._course_id, percent, percent, 1),
                        )

                c.commit()
        except Exception as e:
            print(f"[QUIZ] Ошибка сохранения результата: {e}")

    def _show_results(self, score: int, total: int, percent: float, elapsed: float):
        """Показывает экран результатов."""
        app = self.get_app()
        self.clear_widgets()


        scroll = MDScrollView()
        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12), size_hint_y=None)
        root.bind(minimum_height=root.setter('height'))


        title = MDLabel(
            text="Результаты",
            bold=True,
            halign="center",
            theme_text_color="Custom",
            text_color=app.mm_text,
            font_size=sp(22),
            size_hint_y=None,
            height=dp(36),
        )
        root.add_widget(title)


        if percent >= 90:
            grade = "Отлично!"
            grade_color = (0.3, 0.85, 0.4, 1)
        elif percent >= 70:
            grade = "Хорошо!"
            grade_color = (0.4, 0.75, 0.9, 1)
        elif percent >= 50:
            grade = "Неплохо"
            grade_color = (0.9, 0.75, 0.3, 1)
        else:
            grade = "Нужно повторить"
            grade_color = (0.9, 0.4, 0.35, 1)

        grade_label = MDLabel(
            text=grade,
            bold=True,
            halign="center",
            theme_text_color="Custom",
            text_color=grade_color,
            font_size=sp(26),
            size_hint_y=None,
            height=dp(40),
        )
        root.add_widget(grade_label)


        stats_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(120),
            spacing=dp(8),
            padding=[dp(20), dp(16)],
        )


        with stats_box.canvas.before:
            Color(0.1, 0.12, 0.18, 1)
            stats_box._bg = RoundedRectangle(pos=stats_box.pos, size=stats_box.size, radius=[dp(12)])
        stats_box.bind(pos=lambda *_: setattr(stats_box._bg, 'pos', stats_box.pos),
                       size=lambda *_: setattr(stats_box._bg, 'size', stats_box.size))


        result_label = MDLabel(
            text=f"Правильных ответов: {score} из {total}",
            halign="center",
            theme_text_color="Custom",
            text_color=app.mm_text,
            font_size=sp(16),
            size_hint_y=None,
            height=dp(28),
        )
        stats_box.add_widget(result_label)


        percent_label = MDLabel(
            text=f"{percent:.0f}%",
            bold=True,
            halign="center",
            theme_text_color="Custom",
            text_color=grade_color,
            font_size=sp(36),
            size_hint_y=None,
            height=dp(48),
        )
        stats_box.add_widget(percent_label)


        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        time_text = f"{minutes} мин {seconds} сек" if minutes > 0 else f"{seconds} сек"
        time_label = MDLabel(
            text=f"Время: {time_text}",
            halign="center",
            theme_text_color="Custom",
            text_color=app.mm_text2,
            font_size=sp(13),
            size_hint_y=None,
            height=dp(24),
        )
        stats_box.add_widget(time_label)

        root.add_widget(stats_box)


        root.add_widget(Widget(size_hint_y=None, height=dp(16)))


        buttons_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(160),
            spacing=dp(10),
        )


        review_btn = MDButton(
            style="outlined",
            size_hint=(None, None),
            size=(dp(220), dp(42)),
            pos_hint={"center_x": 0.5},
            on_release=lambda *_: self._show_review(),
        )
        review_btn.add_widget(MDButtonText(text="Посмотреть ответы"))
        buttons_box.add_widget(review_btn)


        retry_btn = MDButton(
            style="filled",
            size_hint=(None, None),
            size=(dp(220), dp(42)),
            pos_hint={"center_x": 0.5},
            md_bg_color=app.mm_primary,
            on_release=lambda *_: self._retry(),
        )
        retry_btn.add_widget(MDButtonText(text="Пройти снова"))
        buttons_box.add_widget(retry_btn)


        back_btn = MDButton(
            style="text",
            size_hint=(None, None),
            size=(dp(180), dp(38)),
            pos_hint={"center_x": 0.5},
            on_release=lambda *_: app.open_quiz_selection(),
        )
        back_btn.add_widget(MDButtonText(text="К викторинам"))
        buttons_box.add_widget(back_btn)

        root.add_widget(buttons_box)


        root.add_widget(Widget(size_hint_y=None, height=dp(20)))

        scroll.add_widget(root)
        self.add_widget(scroll)

    def _show_review(self):
        """Показывает разбор ответов."""
        app = self.get_app()
        self.clear_widgets()

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))


        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44))
        title = MDLabel(
            text="Разбор ответов",
            bold=True,
            halign="left",
            theme_text_color="Custom",
            text_color=app.mm_text,
            font_size=sp(18),
        )
        header.add_widget(title)

        close_btn = MDButton(
            style="text",
            size_hint_x=None,
            width=dp(80),
            on_release=lambda *_: self._load(),
        )
        close_btn.add_widget(MDButtonText(text="Закрыть"))
        header.add_widget(close_btn)
        root.add_widget(header)


        scroll = MDScrollView()
        review_box = BoxLayout(
            orientation="vertical",
            spacing=dp(16),
            size_hint_y=None,
            padding=[0, dp(8), 0, dp(60)],
        )
        review_box.bind(minimum_height=review_box.setter('height'))

        for idx, q in enumerate(self._questions):
            user_answer = self._answers.get(idx)
            is_correct = (user_answer == q.correct)


            card = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                padding=[dp(12), dp(10)],
                spacing=dp(6),
            )
            card.bind(minimum_height=card.setter('height'))


            bg_color = (0.12, 0.18, 0.14, 1) if is_correct else (0.18, 0.12, 0.12, 1)
            with card.canvas.before:
                Color(*bg_color)
                card._bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(10)])
            card.bind(pos=lambda inst, val: setattr(inst._bg, 'pos', val),
                     size=lambda inst, val: setattr(inst._bg, 'size', val))


            status_text = "✓" if is_correct else "✗"
            status_color = (0.4, 0.85, 0.5, 1) if is_correct else (0.9, 0.4, 0.4, 1)

            q_header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(24))
            q_num = MDLabel(
                text=f"Вопрос {idx + 1}",
                bold=True,
                theme_text_color="Custom",
                text_color=app.mm_text,
                font_size=sp(13),
            )
            q_header.add_widget(q_num)

            q_status = MDLabel(
                text=status_text,
                bold=True,
                halign="right",
                theme_text_color="Custom",
                text_color=status_color,
                font_size=sp(18),
                size_hint_x=None,
                width=dp(30),
            )
            q_header.add_widget(q_status)
            card.add_widget(q_header)


            q_text = MDLabel(
                text=q.text,
                theme_text_color="Custom",
                text_color=app.mm_text,
                font_size=sp(14),
                size_hint_y=None,
            )
            q_text.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1] + dp(4)))
            card.add_widget(q_text)


            if user_answer is not None:
                user_text = q.options[user_answer]
                answer_color = (0.4, 0.85, 0.5, 1) if is_correct else (0.9, 0.5, 0.5, 1)
                user_label = MDLabel(
                    text=f"Ваш ответ: {user_text}",
                    theme_text_color="Custom",
                    text_color=answer_color,
                    font_size=sp(13),
                    size_hint_y=None,
                    height=dp(22),
                )
                card.add_widget(user_label)


            if not is_correct:
                correct_label = MDLabel(
                    text=f"Правильный ответ: {q.options[q.correct]}",
                    theme_text_color="Custom",
                    text_color=(0.4, 0.8, 0.5, 1),
                    font_size=sp(13),
                    size_hint_y=None,
                    height=dp(22),
                )
                card.add_widget(correct_label)


            if q.explanation:
                expl_label = MDLabel(
                    text=q.explanation,
                    theme_text_color="Custom",
                    text_color=(0.7, 0.75, 0.8, 1),
                    font_size=sp(12),
                    size_hint_y=None,
                )
                expl_label.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1] + dp(4)))
                card.add_widget(expl_label)

            review_box.add_widget(card)

        scroll.add_widget(review_box)
        root.add_widget(scroll)

        self.add_widget(root)

    def _retry(self):
        """Начинает викторину заново."""
        self._answers = {}
        self._submitted = False
        self._start_time = time.time()


        random.shuffle(self._questions)
        for q in self._questions:
            options = list(q.options)
            correct_text = options[q.correct]
            random.shuffle(options)



        self._load()
