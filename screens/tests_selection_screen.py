from __future__ import annotations

"""
Экран выбора тестов.
Позволяет выбрать тест по темам и видеть прогресс.
"""

import sqlite3
from typing import Any, Dict, List

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout

from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView

from .base_screen import BaseScreen


class TestCard(ButtonBehavior, BoxLayout):
    """Карточка теста."""

    def __init__(self, title: str, color: tuple = None, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(64)
        self.padding = [dp(16), dp(12)]
        self.spacing = dp(2)

        self._on_select = on_select


        bg_color = color if color else (0.13, 0.16, 0.24, 1)

        with self.canvas.before:
            Color(*bg_color)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])

        self.bind(pos=self._update_bg, size=self._update_bg)

        title_label = MDLabel(
            text=title,
            bold=True,
            halign="left",
            valign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_size=sp(15),
            size_hint_y=1,
            shorten=True,
            shorten_from="right",
            max_lines=1,
        )
        self.add_widget(title_label)

    def _update_bg(self, *_):
        if hasattr(self, "_bg"):
            self._bg.pos = self.pos
            self._bg.size = self.size

    def on_release(self):
        if self._on_select:
            self._on_select()


class TestsSelectionScreen(BaseScreen):
    """Выбор теста."""

    def on_pre_enter(self, *args):
        self.title = "Тесты"
        super().on_pre_enter(*args)
        Clock.schedule_once(lambda *_: self._build_ui(), 0)

    def _conn(self) -> sqlite3.Connection:
        app = self.get_app()
        conn = sqlite3.connect(app.courses_db)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_tests(self) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                """
                SELECT
                    q.id as quiz_id,
                    q.title as quiz_title,
                    q.course_id as course_id,
                    q.section_id as section_id,
                    cs.title as section_title,
                    cs.position as section_position,
                    c.title as course_title,
                    COUNT(a.id) as attempts,
                    MAX(a.percent) as best_percent
                FROM mm_quizzes q
                JOIN courses c ON c.id = q.course_id
                LEFT JOIN course_sections cs ON cs.id = q.section_id
                LEFT JOIN mm_quiz_attempts a ON a.quiz_id = q.id
                WHERE q.id > 0
                GROUP BY q.id
                ORDER BY c.id,
                         CASE WHEN q.section_id IS NULL THEN 0 ELSE 1 END,
                         cs.position,
                         q.id
                """
            ).fetchall()

        return [dict(r) for r in rows]

    def _get_overall_stats(self) -> str:
        try:
            with self._conn() as c:
                row = c.execute(
                    """
                    SELECT COUNT(*) as attempts, MAX(percent) as best
                    FROM mm_quiz_attempts
                    WHERE quiz_id IN (SELECT id FROM mm_quizzes WHERE id > 0)
                    """
                ).fetchone()
            if row and row["attempts"]:
                return f"Попыток: {row['attempts']} | Лучший результат: {row['best']:.0f}%"
        except Exception:
            pass
        return ""

    def _build_ui(self):
        self.clear_widgets()
        app = self.get_app()

        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

        header = MDLabel(
            text="Выберите тест",
            halign="center",
            bold=True,
            theme_text_color="Custom",
            text_color=app.mm_text,
            font_size=sp(20),
            size_hint_y=None,
            height=dp(36),
        )
        root.add_widget(header)

        stats_text = self._get_overall_stats()
        if stats_text:
            stats_label = MDLabel(
                text=stats_text,
                halign="center",
                theme_text_color="Custom",
                text_color=app.mm_text2,
                font_size=sp(13),
                size_hint_y=None,
                height=dp(24),
            )
            root.add_widget(stats_label)

        tests = self._load_tests()
        if not tests:
            root.add_widget(
                MDLabel(
                    text="Тесты не найдены",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=app.mm_text2,
                )
            )
            self.add_widget(root)
            return

        scroll = MDScrollView()
        content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None,
            padding=[0, dp(8), 0, dp(16)],
        )
        content.bind(minimum_height=content.setter("height"))


        card_color = (0.45, 0.42, 0.65, 1)

        for test in tests:
            def _make_on_select(test_data: Dict[str, Any]):
                def _on_select():
                    if test_data.get("section_id"):
                        self.get_app().open_quiz_for_section(
                            int(test_data["section_id"]),
                            str(test_data.get("section_title") or "")
                        )
                    else:
                        self.get_app().open_quiz_for_course(int(test_data["course_id"]))
                return _on_select

            card = TestCard(
                title=str(test.get("quiz_title") or "Тест"),
                color=card_color,
                on_select=_make_on_select(test),
            )
            content.add_widget(card)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)
