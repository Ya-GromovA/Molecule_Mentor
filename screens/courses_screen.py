from __future__ import annotations

import sqlite3

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout

from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.progressindicator import MDLinearProgressIndicator
from kivymd.uix.scrollview import MDScrollView

from .base_screen import BaseScreen


class ClickableCard(ButtonBehavior, BoxLayout):
    """Кликабельная карточка для списков курсов."""

    def __init__(self, on_click=None, bg_color=(0.10, 0.12, 0.18, 1), **kwargs):
        super().__init__(**kwargs)
        self._on_click = on_click
        self._bg_color = bg_color
        self._pressed_color = (
            min(1.0, bg_color[0] + 0.08),
            min(1.0, bg_color[1] + 0.08),
            min(1.0, bg_color[2] + 0.08),
            bg_color[3],
        )

        with self.canvas.before:
            self._color_instr = Color(*self._bg_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[18, 18, 18, 18])

        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def on_press(self):
        self._color_instr.rgba = self._pressed_color

    def on_release(self):
        self._color_instr.rgba = self._bg_color
        if self._on_click:
            self._on_click()


class ProgressCard(BoxLayout):
    """Карточка с общим прогрессом тестирования."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(130)
        self.padding = [dp(16), dp(14), dp(16), dp(14)]
        self.spacing = dp(8)

        # Фон карточки
        with self.canvas.before:
            Color(0.08, 0.10, 0.16, 1)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])

        self.bind(pos=self._update_bg, size=self._update_bg)

        # Заголовок
        self._title = MDLabel(
            text="Мой прогресс",
            halign="left",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            bold=True,
            font_size=dp(18),
            size_hint_y=None,
            height=dp(26),
        )
        self.add_widget(self._title)

        # Строка с лучшим результатом
        self._best_label = MDLabel(
            text="Лучший результат: —",
            halign="left",
            theme_text_color="Custom",
            text_color=(0.7, 0.75, 0.85, 1),
            font_size=dp(14),
            size_hint_y=None,
            height=dp(22),
        )
        self.add_widget(self._best_label)

        # Прогресс-бар
        self._progress_bar = MDLinearProgressIndicator(
            value=0,
            size_hint_y=None,
            height=dp(6),
        )
        self.add_widget(self._progress_bar)

        # Строка со статистикой
        self._stats_label = MDLabel(
            text="",
            halign="left",
            theme_text_color="Custom",
            text_color=(0.5, 0.55, 0.65, 1),
            font_size=dp(12),
            size_hint_y=None,
            height=dp(20),
        )
        self.add_widget(self._stats_label)

    def _update_bg(self, *_):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def set_progress(self, best_percent: float, last_percent: float, attempts: int):
        """Обновляет отображение прогресса."""
        if attempts == 0:
            self._best_label.text = "Тесты ещё не пройдены"
            self._progress_bar.value = 0
            self._stats_label.text = "Пройдите тест после изучения курса"
        else:
            self._best_label.text = f"Лучший результат: {best_percent:.0f}%"
            self._progress_bar.value = best_percent / 100.0
            
            # Цвет прогресс-бара в зависимости от результата
            if best_percent >= 80:
                self._progress_bar.indicator_color = (0.2, 0.8, 0.4, 1)  # Зелёный
            elif best_percent >= 50:
                self._progress_bar.indicator_color = (0.9, 0.7, 0.2, 1)  # Жёлтый
            else:
                self._progress_bar.indicator_color = (0.9, 0.3, 0.3, 1)  # Красный
            
            attempts_word = self._pluralize(attempts, "попытка", "попытки", "попыток")
            self._stats_label.text = f"Последний: {last_percent:.0f}% · {attempts} {attempts_word}"

    @staticmethod
    def _pluralize(n: int, one: str, few: str, many: str) -> str:
        """Склонение слова по числу."""
        if 11 <= n % 100 <= 19:
            return many
        last = n % 10
        if last == 1:
            return one
        if 2 <= last <= 4:
            return few
        return many


class CourseCard(ButtonBehavior, BoxLayout):
    """Простая кликабельная карточка курса."""

    def __init__(self, title: str, on_click=None, bg_color=(0.10, 0.12, 0.18, 1), **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(64)
        self.padding = [dp(16), dp(12), dp(16), dp(12)]
        self.spacing = dp(12)
        
        self._on_click = on_click
        self._bg_color = bg_color
        self._pressed_color = (
            min(1.0, bg_color[0] + 0.08),
            min(1.0, bg_color[1] + 0.08),
            min(1.0, bg_color[2] + 0.08),
            bg_color[3],
        )

        # Фон карточки
        with self.canvas.before:
            self._color_instr = Color(*bg_color)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])

        self.bind(pos=self._update_bg, size=self._update_bg)

        # Название курса
        self._title_label = MDLabel(
            text=title,
            halign="left",
            valign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            bold=True,
            font_size=dp(16),
        )
        self.add_widget(self._title_label)
        
        # Стрелка (>)
        arrow_label = MDLabel(
            text=">",
            halign="right",
            valign="center",
            theme_text_color="Custom",
            text_color=(0.6, 0.65, 0.75, 1),
            font_size=dp(20),
            bold=True,
            size_hint_x=None,
            width=dp(24),
        )
        self.add_widget(arrow_label)

    def _update_bg(self, *_):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def on_press(self):
        self._color_instr.rgba = self._pressed_color

    def on_release(self):
        self._color_instr.rgba = self._bg_color
        if self._on_click:
            self._on_click()


class CoursesScreen(BaseScreen):
    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        Clock.schedule_once(lambda *_: self._load(), 0)

    def _get_total_progress(self) -> tuple[float, float, int]:
        """Получает общий прогресс по всем курсам."""
        app = self.get_app()
        try:
            conn = sqlite3.connect(app.courses_db)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            row = cur.execute("""
                SELECT 
                    MAX(best_percent) as best,
                    (SELECT last_percent FROM mm_course_progress ORDER BY updated_at DESC LIMIT 1) as last,
                    SUM(attempts_count) as attempts
                FROM mm_course_progress
            """).fetchone()

            conn.close()

            if row and row["attempts"]:
                return float(row["best"] or 0), float(row["last"] or 0), int(row["attempts"] or 0)
        except Exception as e:
            print(f"[CoursesScreen] Error loading progress: {e}")
        
        return 0.0, 0.0, 0

    def _load(self):
        app = self.get_app()
        repo = app.course_repo

        self.title = "Курсы"
        app.set_top_title("Курсы")

        self.clear_widgets()
        
        # Фон
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))
        with root.canvas.before:
            Color(*app.mm_bg)
            self._root_bg = RoundedRectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *_: setattr(self._root_bg, 'pos', root.pos),
                  size=lambda *_: setattr(self._root_bg, 'size', root.size))

        # Карточка прогресса тестирования
        best, last, attempts = self._get_total_progress()
        progress_card = ProgressCard()
        progress_card.set_progress(best, last, attempts)
        root.add_widget(progress_card)

        # Кнопка "Пройти тест"
        test_btn_row = BoxLayout(size_hint_y=None, height=dp(48), padding=[0, dp(4), 0, dp(4)])
        test_btn = MDButton(style="filled", on_release=lambda *_: app.open_quiz_for_course(1))
        test_btn.add_widget(MDButtonText(text="Пройти тест"))
        test_btn_row.add_widget(test_btn)
        root.add_widget(test_btn_row)

        # Заголовок списка курсов
        courses_header = MDLabel(
            text="Доступные курсы",
            halign="left",
            theme_text_color="Custom",
            text_color=app.mm_text,
            bold=True,
            font_size=dp(16),
            size_hint_y=None,
            height=dp(28),
            padding=[dp(4), 0, 0, 0],
        )
        root.add_widget(courses_header)

        # Список курсов
        courses = repo.list_courses()
        if not courses:
            root.add_widget(
                MDLabel(
                    text="Курсы не найдены",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=app.mm_text2,
                )
            )
            self.add_widget(root)
            return

        scroll = MDScrollView()
        col = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10), padding=[0, dp(4), 0, dp(4)])
        col.bind(minimum_height=col.setter("height"))

        for c in courses:
            course_id = int(c.id)
            course_title = str(c.title)
            
            # Простая карточка курса
            card = CourseCard(
                title=course_title,
                on_click=lambda cid=course_id, ct=course_title: app.open_course(cid, ct),
                bg_color=app.mm_surface,
            )
            col.add_widget(card)

        scroll.add_widget(col)
        root.add_widget(scroll)
        self.add_widget(root)
