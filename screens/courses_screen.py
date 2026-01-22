from __future__ import annotations

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from kivymd.uix.label import MDLabel
from kivymd.uix.list import (
    MDList,
    MDListItem,
    MDListItemHeadlineText,
    MDListItemSupportingText,
)
from kivymd.uix.scrollview import MDScrollView

from .base_screen import BaseScreen


class CoursesScreen(BaseScreen):
    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        Clock.schedule_once(lambda *_: self._load(), 0)

    def _progress_text(self, c) -> str:
        """
        Формирует строку прогресса, не падая, даже если в Course нет нужных полей.
        Берём прогресс через repo.get_course_progress(course_id).
        """
        app = self.get_app()
        repo = app.course_repo

        try:
            best, last, attempts = repo.get_course_progress(int(c.id))
        except Exception:
            return "Прогресс: нет данных"

        parts = [
            f"лучший {best:.0f}%",
            f"последний {last:.0f}%",
            f"попыток {int(attempts)}",
        ]
        return "Прогресс: " + ", ".join(parts)

    def _style_list_item(
        self,
        item: MDListItem,
        headline: MDListItemHeadlineText | None = None,
        supporting: MDListItemSupportingText | None = None,
    ) -> None:
        """Единый стиль элементов списка под тёмную тему приложения."""
        app = self.get_app()

        item.theme_bg_color = "Custom"
        item.md_bg_color = app.mm_surface
        item.radius = [dp(18), dp(18), dp(18), dp(18)]
        item.padding = [dp(16), dp(12), dp(16), dp(12)]

        if headline is not None:
            headline.theme_text_color = "Custom"
            headline.text_color = app.mm_text
        if supporting is not None:
            supporting.theme_text_color = "Custom"
            supporting.text_color = app.mm_text2

    def _load(self):
        app = self.get_app()
        repo = app.course_repo

        self.title = "Курсы"
        app.set_top_title("Курсы")

        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))

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
        lst = MDList(spacing=dp(10), padding=[0, dp(6), 0, dp(6)])

        for c in courses:
            item = MDListItem(
                on_release=lambda _w, cid=int(c.id), ct=str(c.title): app.open_course(cid, ct)
            )
            headline = MDListItemHeadlineText(text=str(c.title))
            supporting = MDListItemSupportingText(text=self._progress_text(c))

            item.add_widget(headline)
            item.add_widget(supporting)
            self._style_list_item(item, headline, supporting)

            lst.add_widget(item)

        scroll.add_widget(lst)
        root.add_widget(scroll)
        self.add_widget(root)
