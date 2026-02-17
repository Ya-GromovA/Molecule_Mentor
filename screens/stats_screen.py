from __future__ import annotations

"""
Экран статистики и достижений.
Показывает прогресс пользователя в викторинах.
"""

import sqlite3
from typing import List, Dict, Any

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.progressindicator import MDCircularProgressIndicator

from .base_screen import BaseScreen



ACHIEVEMENTS = [
    {
        "id": "first_quiz",
        "title": "Первые шаги",
        "description": "Пройдите первую викторину",
        "condition": lambda stats: stats.get("total_attempts", 0) >= 1,
    },
    {
        "id": "quiz_5",
        "title": "Любознательный",
        "description": "Пройдите 5 викторин",
        "condition": lambda stats: stats.get("total_attempts", 0) >= 5,
    },
    {
        "id": "quiz_10",
        "title": "Знаток",
        "description": "Пройдите 10 викторин",
        "condition": lambda stats: stats.get("total_attempts", 0) >= 10,
    },
    {
        "id": "quiz_25",
        "title": "Эксперт",
        "description": "Пройдите 25 викторин",
        "condition": lambda stats: stats.get("total_attempts", 0) >= 25,
    },
    {
        "id": "perfect_score",
        "title": "Отличник",
        "description": "Получите 100% в любой викторине",
        "condition": lambda stats: stats.get("best_percent", 0) >= 100,
    },
    {
        "id": "high_score_90",
        "title": "Почти идеально",
        "description": "Получите 90%+ в викторине",
        "condition": lambda stats: stats.get("best_percent", 0) >= 90,
    },
    {
        "id": "correct_50",
        "title": "Полсотни верных",
        "description": "Дайте 50 правильных ответов",
        "condition": lambda stats: stats.get("total_correct", 0) >= 50,
    },
    {
        "id": "correct_100",
        "title": "Сотня верных",
        "description": "Дайте 100 правильных ответов",
        "condition": lambda stats: stats.get("total_correct", 0) >= 100,
    },
    {
        "id": "organic_master",
        "title": "Органик",
        "description": "Пройдите викторину по органике на 80%+",
        "condition": lambda stats: stats.get("organic_best", 0) >= 80,
    },
    {
        "id": "inorganic_master",
        "title": "Неорганик",
        "description": "Пройдите викторину по неорганике на 80%+",
        "condition": lambda stats: stats.get("inorganic_best", 0) >= 80,
    },
    {
        "id": "molecules_master",
        "title": "Молекулярщик",
        "description": "Пройдите викторину по молекулам на 80%+",
        "condition": lambda stats: stats.get("molecules_best", 0) >= 80,
    },
    {
        "id": "hardcore_pass",
        "title": "Храбрец",
        "description": "Пройдите сложный тест на 50%+",
        "condition": lambda stats: stats.get("hardcore_best", 0) >= 50,
    },
]


class AchievementCard(BoxLayout):
    """Карточка достижения."""

    def __init__(self, achievement: dict, unlocked: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(58)
        self.padding = [dp(12), dp(8)]
        self.spacing = dp(4)


        bg_color = (0.15, 0.2, 0.15, 1) if unlocked else (0.12, 0.12, 0.15, 1)
        with self.canvas.before:
            Color(*bg_color)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self._update_bg, size=self._update_bg)

        title_color = (0.9, 0.95, 0.7, 1) if unlocked else (0.5, 0.5, 0.55, 1)
        title = MDLabel(
            text=achievement["title"],
            bold=True,
            theme_text_color="Custom",
            text_color=title_color,
            font_size=sp(14),
            size_hint_y=None,
            height=dp(22),
        )
        self.add_widget(title)

        desc_color = (0.7, 0.75, 0.65, 1) if unlocked else (0.45, 0.45, 0.5, 1)
        desc = MDLabel(
            text=achievement["description"],
            theme_text_color="Custom",
            text_color=desc_color,
            font_size=sp(12),
            size_hint_y=None,
            height=dp(20),
        )
        self.add_widget(desc)

    def _update_bg(self, *_):
        if hasattr(self, '_bg'):
            self._bg.pos = self.pos
            self._bg.size = self.size


class StatsScreen(BaseScreen):
    """Статистика и достижения."""

    def on_pre_enter(self, *args):
        self.title = "Статистика"
        super().on_pre_enter(*args)
        Clock.schedule_once(lambda *_: self._build_ui(), 0)

    def _conn(self) -> sqlite3.Connection:
        app = self.get_app()
        conn = sqlite3.connect(app.courses_db)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_stats(self) -> Dict[str, Any]:
        """Получает статистику из базы данных."""
        stats = {
            "total_attempts": 0,
            "total_correct": 0,
            "total_questions": 0,
            "best_percent": 0,
            "avg_percent": 0,
            "organic_best": 0,
            "inorganic_best": 0,
            "molecules_best": 0,
            "hardcore_best": 0,
        }

        try:
            with self._conn() as c:

                row = c.execute("""
                    SELECT
                        COUNT(*) as attempts,
                        SUM(score) as correct,
                        SUM(total) as questions,
                        MAX(percent) as best,
                        AVG(percent) as avg
                    FROM mm_quiz_attempts
                """).fetchone()

                if row and row["attempts"]:
                    stats["total_attempts"] = row["attempts"] or 0
                    stats["total_correct"] = row["correct"] or 0
                    stats["total_questions"] = row["questions"] or 0
                    stats["best_percent"] = row["best"] or 0
                    stats["avg_percent"] = row["avg"] or 0

        except Exception as e:
            print(f"[STATS] Ошибка получения статистики: {e}")

        return stats

    def _build_ui(self):
        """Строит интерфейс экрана статистики."""
        self.clear_widgets()
        app = self.get_app()
        stats = self._get_stats()

        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

        scroll = MDScrollView()
        content = BoxLayout(
            orientation="vertical",
            spacing=dp(16),
            size_hint_y=None,
            padding=[0, 0, 0, dp(20)],
        )
        content.bind(minimum_height=content.setter('height'))


        stats_section = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
            padding=[dp(16), dp(16)],
        )
        stats_section.bind(minimum_height=stats_section.setter('height'))


        with stats_section.canvas.before:
            Color(0.1, 0.12, 0.18, 1)
            stats_section._bg = RoundedRectangle(
                pos=stats_section.pos, size=stats_section.size, radius=[dp(12)]
            )
        stats_section.bind(
            pos=lambda *_: setattr(stats_section._bg, 'pos', stats_section.pos),
            size=lambda *_: setattr(stats_section._bg, 'size', stats_section.size)
        )


        header = MDLabel(
            text="Ваш прогресс",
            bold=True,
            theme_text_color="Custom",
            text_color=app.mm_text,
            font_size=sp(18),
            size_hint_y=None,
            height=dp(30),
        )
        stats_section.add_widget(header)


        stat_items = [
            ("Пройдено викторин", str(stats["total_attempts"])),
            ("Правильных ответов", str(stats["total_correct"])),
            ("Всего вопросов", str(stats["total_questions"])),
            ("Лучший результат", f"{stats['best_percent']:.0f}%"),
            ("Средний результат", f"{stats['avg_percent']:.0f}%"),
        ]

        for label, value in stat_items:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28))

            label_widget = MDLabel(
                text=label,
                theme_text_color="Custom",
                text_color=app.mm_text2,
                font_size=sp(14),
            )
            row.add_widget(label_widget)

            value_widget = MDLabel(
                text=value,
                bold=True,
                halign="right",
                theme_text_color="Custom",
                text_color=app.mm_accent,
                font_size=sp(14),
                size_hint_x=None,
                width=dp(80),
            )
            row.add_widget(value_widget)

            stats_section.add_widget(row)

        content.add_widget(stats_section)


        achievements_header = MDLabel(
            text="Достижения",
            bold=True,
            theme_text_color="Custom",
            text_color=app.mm_text,
            font_size=sp(18),
            size_hint_y=None,
            height=dp(36),
            padding=[dp(4), 0],
        )
        content.add_widget(achievements_header)


        unlocked_count = sum(1 for a in ACHIEVEMENTS if a["condition"](stats))
        total_count = len(ACHIEVEMENTS)

        counter_label = MDLabel(
            text=f"Получено: {unlocked_count} из {total_count}",
            theme_text_color="Custom",
            text_color=app.mm_text2,
            font_size=sp(13),
            size_hint_y=None,
            height=dp(24),
            padding=[dp(4), 0],
        )
        content.add_widget(counter_label)


        for achievement in ACHIEVEMENTS:
            unlocked = achievement["condition"](stats)
            card = AchievementCard(achievement=achievement, unlocked=unlocked)
            content.add_widget(card)

        scroll.add_widget(content)
        root.add_widget(scroll)

        self.add_widget(root)
