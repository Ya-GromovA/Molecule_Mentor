
from __future__ import annotations

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout

from kivymd.uix.label import MDLabel
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
        Logger.info("[ClickableCard] on_press")

    def on_release(self):
        self._color_instr.rgba = self._bg_color
        Logger.info(f"[ClickableCard] on_release, has callback: {self._on_click is not None}")
        if self._on_click:
            self._on_click()


class CourseTopicScreen(BaseScreen):
    """
    Универсальный экран “Курс/Раздел/Тема”:

    nav_state:
      - course_id, course_title -> показываем разделы
      - section_id, section_title -> показываем темы
      - topic_id, topic_title -> показываем blocks (теорию)
    """

    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        Clock.schedule_once(lambda *_: self._render(), 0)

    # ---------------- оформление UI ----------------

    def _make_clickable_item(self, title: str, subtitle: str = None, on_click=None) -> ClickableCard:
        """Создаёт кликабельный элемент списка."""
        app = self.get_app()

        card = ClickableCard(
            on_click=on_click,
            bg_color=app.mm_surface,
            orientation="vertical",
            size_hint_y=None,
            height=dp(72) if subtitle else dp(56),
            padding=[dp(16), dp(12), dp(16), dp(12)],
        )

        headline = MDLabel(
            text=title,
            theme_text_color="Custom",
            text_color=app.mm_text,
            font_size=dp(16),
            bold=True,
            size_hint_y=None,
            height=dp(24),
        )
        card.add_widget(headline)

        if subtitle:
            supporting = MDLabel(
                text=subtitle,
                theme_text_color="Custom",
                text_color=app.mm_text2,
                font_size=dp(14),
                size_hint_y=None,
                height=dp(20),
            )
            card.add_widget(supporting)

        return card

    def _make_root(self) -> BoxLayout:
        app = self.get_app()
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        # фон как у тёмных экранов
        bg_rgba = getattr(app, "mm_bg", None) or getattr(app, "mm_surface", None) or (0.06, 0.07, 0.09, 1)
        with root.canvas.before:
            self._bg_color = Color(*bg_rgba)
            self._bg_rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_bg, size=self._update_bg)

        return root

    def _update_bg(self, *_):
        if hasattr(self, "_bg_rect"):
            self._bg_rect.pos = self.parent.pos if self.parent else self.pos
            self._bg_rect.size = self.size

    # ---------------- отрисовка ----------------

    def _render(self):
        app = self.get_app()
        repo = app.course_repo
        st = dict(getattr(app, "nav_state", {}) or {})

        course_id = st.get("course_id")
        course_title = st.get("course_title") or "Курс"
        section_id = st.get("section_id")
        section_title = st.get("section_title") or "Раздел"

        Logger.info(f"[CourseTopicScreen] nav_state: course_id={course_id}, section_id={section_id}")

        self.clear_widgets()
        root = self._make_root()

        # ---- MODE 1: раздел -> темы
        if section_id is not None:
            self.title = str(section_title)
            app.set_top_title(self.title)

            topics = repo.list_topics(int(section_id))
            if not topics:
                root.add_widget(
                    MDLabel(
                        text="Темы не найдены",
                        halign="center",
                        theme_text_color="Custom",
                        text_color=app.mm_text2,
                    )
                )
                self.add_widget(root)
                return

            scroll = MDScrollView()
            col = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10), padding=[0, dp(6), 0, dp(6)])
            col.bind(minimum_height=col.setter("height"))

            # Список тем раздела (без кнопки теста - тесты в викторинах)
            for t in topics:
                item = self._make_clickable_item(
                    title=str(t.title),
                    on_click=lambda tid=t.id, tt=t.title: app.open_topic(int(tid), str(tt)),
                )
                col.add_widget(item)

            scroll.add_widget(col)
            root.add_widget(scroll)
            self.add_widget(root)
            return

        # ---- MODE 3: курс -> разделы
        if course_id is None:
            root.add_widget(
                MDLabel(
                    text="Курс не выбран",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=app.mm_text2,
                )
            )
            self.add_widget(root)
            return

        self.title = str(course_title)
        app.set_top_title(self.title)

        sections = repo.list_sections(int(course_id))
        if not sections:
            root.add_widget(
                MDLabel(
                    text="Разделы не найдены",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=app.mm_text2,
                )
            )
            self.add_widget(root)
            return

        scroll = MDScrollView()
        col = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10), padding=[0, dp(6), 0, dp(6)])
        col.bind(minimum_height=col.setter("height"))

        for s in sections:
            item = self._make_clickable_item(
                title=str(s.title),
                on_click=lambda sid=s.id, stt=s.title: app.open_section(int(sid), str(stt)),
            )
            col.add_widget(item)

        scroll.add_widget(col)
        root.add_widget(scroll)
        self.add_widget(root)
