from __future__ import annotations

import random

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout

from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView

from data.quiz_questions import QUESTIONS
from .base_screen import BaseScreen


class ExamPrepScreen(BaseScreen):
    def on_pre_enter(self, *args):
        self.title = "Подготовка к ОГЭ/ЕГЭ"
        super().on_pre_enter(*args)
        Clock.schedule_once(lambda *_: self._build_ui(), 0)

    def _pick_questions(self, count: int, min_diff: int, max_diff: int) -> list[dict]:
        pool = [q for q in QUESTIONS if min_diff <= int(q.get("difficulty", 1)) <= max_diff]
        random.shuffle(pool)
        return pool[: min(count, len(pool))]

    def _start(self, mode: str):
        app = self.get_app()
        if mode == "oge":
            qs = self._pick_questions(count=18, min_diff=1, max_diff=2)
            app.open_custom_quiz("ОГЭ: тренировочный вариант", qs, return_screen="exam_prep")
            return
        if mode == "ege_basic":
            qs = self._pick_questions(count=22, min_diff=2, max_diff=3)
            app.open_custom_quiz("ЕГЭ: базовый тренировочный вариант", qs, return_screen="exam_prep")
            return
        qs = self._pick_questions(count=28, min_diff=2, max_diff=3)
        app.open_custom_quiz("ЕГЭ: профильный тренировочный вариант", qs, return_screen="exam_prep")

    def _mode_card(self, title: str, subtitle: str, btn_text: str, mode: str, color: tuple[float, float, float, float]) -> BoxLayout:
        app = self.get_app()
        card = BoxLayout(orientation="vertical", size_hint_y=None, padding=[dp(14), dp(12)], spacing=dp(8), height=dp(118))
        with card.canvas.before:
            Color(*color)
            bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(14)])
        card.bind(pos=lambda *_: setattr(bg, "pos", card.pos), size=lambda *_: setattr(bg, "size", card.size))

        card.add_widget(
            MDLabel(
                text=title,
                bold=True,
                theme_text_color="Custom",
                text_color=app.mm_text,
                font_size=sp(16),
                size_hint_y=None,
                height=dp(26),
            )
        )
        card.add_widget(
            MDLabel(
                text=subtitle,
                theme_text_color="Custom",
                text_color=app.mm_text2,
                font_size=sp(12),
                size_hint_y=None,
                height=dp(34),
            )
        )
        btn = MDButton(style="filled", size_hint=(None, None), size=(dp(240), dp(38)), pos_hint={"center_x": 0.5})
        btn.add_widget(MDButtonText(text=btn_text))
        btn.bind(on_release=lambda *_: self._start(mode))
        card.add_widget(btn)
        return card

    def _build_ui(self):
        self.clear_widgets()
        app = self.get_app()

        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        with root.canvas.before:
            Color(*app.mm_bg)
            self._bg = RoundedRectangle(pos=root.pos, size=root.size, radius=[0])
        root.bind(pos=lambda *_: setattr(self._bg, "pos", root.pos), size=lambda *_: setattr(self._bg, "size", root.size))

        scroll = MDScrollView(do_scroll_x=False, do_scroll_y=True)
        content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            padding=[0, dp(4), 0, dp(10)],
        )
        content.bind(minimum_height=content.setter("height"))

        content.add_widget(
            MDLabel(
                text="Режим подготовки к экзаменам",
                bold=True,
                halign="center",
                theme_text_color="Custom",
                text_color=app.mm_text,
                font_size=sp(20),
                size_hint_y=None,
                height=dp(34),
            )
        )
        content.add_widget(
            MDLabel(
                text="Подбор вопросов идет из общей базы по сложности",
                halign="center",
                theme_text_color="Custom",
                text_color=app.mm_text2,
                font_size=sp(12),
                size_hint_y=None,
                height=dp(20),
            )
        )

        content.add_widget(self._mode_card(
            "ОГЭ (9 класс)",
            "Тренировочный вариант: базовый и средний уровень",
            "Начать ОГЭ-вариант",
            "oge",
            (0.13, 0.18, 0.28, 1),
        ))
        content.add_widget(self._mode_card(
            "ЕГЭ (11 класс, базовый уровень)",
            "Тренировочный вариант: средний и повышенный уровень",
            "Начать ЕГЭ базовый",
            "ege_basic",
            (0.16, 0.15, 0.27, 1),
        ))
        content.add_widget(self._mode_card(
            "ЕГЭ (11 класс, профильный уровень)",
            "Тренировочный вариант: сложные задания",
            "Начать ЕГЭ профильный",
            "ege_profile",
            (0.19, 0.13, 0.24, 1),
        ))

        scroll.add_widget(content)
        root.add_widget(scroll)

        self.add_widget(root)
