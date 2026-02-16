from __future__ import annotations

"""
Экран выбора викторин.
Позволяет выбрать категорию викторины.
"""

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout

from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView

from .base_screen import BaseScreen


# Категории викторин
QUIZ_CATEGORIES = [
    {
        "id": "quick",
        "title": "Быстрая викторина",
        "subtitle": "Отлично для разминки!",
        "color": (0.95, 0.75, 0.2, 1),
        "questions_count": 10,
    },
    {
        "id": "organic",
        "title": "Органическая химия",
        "subtitle": "Углеводороды, спирты, кислоты",
        "color": (0.3, 0.75, 0.45, 1),
        "questions_count": 15,
    },
    {
        "id": "inorganic",
        "title": "Неорганическая химия",
        "subtitle": "Кислоты, основания, соли",
        "color": (0.35, 0.55, 0.9, 1),
        "questions_count": 15,
    },
    {
        "id": "molecules",
        "title": "Молекулы",
        "subtitle": "Формулы, свойства, применение",
        "color": (0.8, 0.4, 0.7, 1),
        "questions_count": 15,
    },
    {
        "id": "reactions",
        "title": "Химические реакции",
        "subtitle": "Типы и продукты реакций",
        "color": (0.9, 0.45, 0.3, 1),
        "questions_count": 12,
    },
    {
        "id": "theory",
        "title": "Теория и понятия",
        "subtitle": "Строение атома, связи",
        "color": (0.5, 0.65, 0.8, 1),
        "questions_count": 12,
    },
    {
        "id": "hardcore",
        "title": "Сложный тест",
        "subtitle": "Только для смелых!",
        "color": (0.7, 0.25, 0.25, 1),
        "questions_count": 20,
    },
]


class CategoryCard(ButtonBehavior, BoxLayout):
    """Карточка категории викторины."""

    def __init__(self, category: dict, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(56)
        self.padding = [dp(12), dp(8)]
        self.spacing = dp(2)

        self._category = category
        self._on_select = on_select
        self._color = category.get("color", (0.3, 0.3, 0.4, 1))

        # Фон карточки
        with self.canvas.before:
            Color(*self._color[:3], 0.25)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])

        self.bind(pos=self._update_rect, size=self._update_rect)

        # Заголовок с количеством вопросов
        title_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
        
        title_label = MDLabel(
            text=category["title"],
            bold=True,
            halign="left",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_size=sp(14),
        )
        title_row.add_widget(title_label)

        count_label = MDLabel(
            text=f"{category['questions_count']} вопр.",
            halign="right",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.8, 1),
            font_size=sp(11),
            size_hint_x=None,
            width=dp(60),
        )
        title_row.add_widget(count_label)

        self.add_widget(title_row)

        # Краткий подзаголовок
        subtitle_text = category.get("subtitle", "")
        if subtitle_text:
            subtitle_label = MDLabel(
                text=subtitle_text,
                halign="left",
                theme_text_color="Custom",
                text_color=(0.75, 0.75, 0.8, 1),
                font_size=sp(11),
                size_hint_y=None,
                height=dp(18),
            )
            self.add_widget(subtitle_label)

    def _update_rect(self, *_):
        if hasattr(self, '_bg_rect'):
            self._bg_rect.pos = self.pos
            self._bg_rect.size = self.size

    def on_release(self):
        if self._on_select:
            self._on_select(self._category)


class QuizSelectionScreen(BaseScreen):
    """Экран выбора викторины."""

    def on_pre_enter(self, *args):
        self.title = "Викторины"
        super().on_pre_enter(*args)
        Clock.schedule_once(lambda *_: self._build_ui(), 0)

    def _build_ui(self):
        self.clear_widgets()
        app = self.get_app()

        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

        # Заголовок
        header = MDLabel(
            text="Выберите викторину",
            halign="center",
            bold=True,
            theme_text_color="Custom",
            text_color=app.mm_text,
            font_size=sp(20),
            size_hint_y=None,
            height=dp(36),
        )
        root.add_widget(header)

        # Статистика (если есть)
        stats = self._get_stats()
        if stats:
            stats_label = MDLabel(
                text=stats,
                halign="center",
                theme_text_color="Custom",
                text_color=app.mm_text2,
                font_size=sp(13),
                size_hint_y=None,
                height=dp(24),
            )
            root.add_widget(stats_label)

        # Кнопка статистики
        stats_btn = MDButton(
            style="outlined",
            size_hint=(None, None),
            size=(dp(160), dp(38)),
            pos_hint={"center_x": 0.5},
            on_release=lambda *_: app.open_stats(),
        )
        stats_btn.add_widget(MDButtonText(text="Моя статистика"))
        root.add_widget(stats_btn)

        # Список категорий
        scroll = MDScrollView()
        categories_box = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None,
            padding=[0, dp(8), 0, dp(16)],
        )
        categories_box.bind(minimum_height=categories_box.setter('height'))

        for cat in QUIZ_CATEGORIES:
            card = CategoryCard(
                category=cat,
                on_select=self._on_category_select,
            )
            categories_box.add_widget(card)

        scroll.add_widget(categories_box)
        root.add_widget(scroll)

        self.add_widget(root)

    def _get_stats(self) -> str:
        """Получает общую статистику по викторинам."""
        try:
            import sqlite3
            app = self.get_app()
            conn = sqlite3.connect(app.courses_db)
            conn.row_factory = sqlite3.Row
            
            row = conn.execute("""
                SELECT COUNT(*) as attempts, 
                       MAX(percent) as best,
                       AVG(percent) as avg
                FROM mm_quiz_attempts
            """).fetchone()
            
            conn.close()
            
            if row and row["attempts"] > 0:
                return f"Пройдено: {row['attempts']} | Лучший: {row['best']:.0f}% | Средний: {row['avg']:.0f}%"
        except Exception:
            pass
        return ""

    def _on_category_select(self, category: dict):
        """Обработчик выбора категории."""
        app = self.get_app()
        app.nav_state = {
            "quiz_category": category["id"],
            "quiz_title": category["title"],
            "quiz_count": category["questions_count"],
        }
        app.open_quiz_standalone()
