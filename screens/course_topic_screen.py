# /home/ulyashka_88/molecule-mentor/screens/course_topic_screen.py
from __future__ import annotations

from pathlib import Path

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.list import (
    MDList,
    MDListItem,
    MDListItemHeadlineText,
    MDListItemSupportingText,
)
from kivymd.uix.scrollview import MDScrollView

from .base_screen import BaseScreen


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

    # ---------------- UI styling ----------------

    def _style_list_item(
        self,
        item: MDListItem,
        headline: MDListItemHeadlineText | None = None,
        supporting: MDListItemSupportingText | None = None,
    ) -> None:
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

    def _make_root(self) -> BoxLayout:
        app = self.get_app()
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        # фон как у тёмных экранов (молекулы/реакции)
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

    # ---------------- data helpers ----------------

    def _content_base_dir(self) -> Path:
        """
        База для относительных путей в topic_blocks.content.
        Обычно всё лежит рядом с courses.db: /data/courses/
        """
        app = self.get_app()
        try:
            db_path = Path(app.courses_db)  # в main.py это строка пути
            return db_path.parent
        except Exception:
            return Path.cwd()

    def _resolve_block_path(self, raw: str) -> str:
        if not raw:
            return ""
        p = Path(raw)
        if p.is_absolute():
            return str(p)
        return str((self._content_base_dir() / p).resolve())

    # ---------------- render ----------------

    def _render(self):
        app = self.get_app()
        repo = app.course_repo
        st = dict(getattr(app, "nav_state", {}) or {})

        course_id = st.get("course_id")
        course_title = st.get("course_title") or "Курс"
        section_id = st.get("section_id")
        section_title = st.get("section_title") or "Раздел"
        topic_id = st.get("topic_id")
        topic_title = st.get("topic_title") or "Тема"

        self.clear_widgets()
        root = self._make_root()

        # ---- MODE 1: topic -> blocks (теория)
        if topic_id is not None:
            self.title = str(topic_title)
            app.set_top_title(self.title)

            blocks = repo.list_blocks(int(topic_id))
            if not blocks:
                root.add_widget(
                    MDLabel(
                        text="Материал темы пока пуст",
                        halign="center",
                        theme_text_color="Custom",
                        text_color=app.mm_text2,
                    )
                )
                self.add_widget(root)
                return

            scroll = MDScrollView(do_scroll_x=False)
            col = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10), padding=(0, 0))
            col.bind(minimum_height=col.setter("height"))

            for b in blocks:
                card = MDCard(
                    orientation="vertical",
                    size_hint_y=None,
                    padding=dp(14),
                    radius=[dp(18), dp(18), dp(18), dp(18)],
                    md_bg_color=app.mm_surface,
                )

                if b.block_type == "image":
                    img_path = self._resolve_block_path(str(b.content))
                    if img_path and Path(img_path).exists():
                        img = Image(source=img_path, allow_stretch=True, keep_ratio=True, size_hint_y=None)
                        img.height = dp(220)
                        card.add_widget(img)
                    else:
                        card.add_widget(
                            MDLabel(
                                text=f"[картинка не найдена]\n{b.content}",
                                theme_text_color="Custom",
                                text_color=app.mm_text2,
                            )
                        )

                    if b.caption:
                        card.add_widget(
                            MDLabel(
                                text=str(b.caption),
                                theme_text_color="Custom",
                                text_color=app.mm_text2,
                                size_hint_y=None,
                            )
                        )
                else:
                    # text by default
                    card.add_widget(
                        MDLabel(
                            text=str(b.content or "").strip(),
                            theme_text_color="Custom",
                            text_color=app.mm_text,
                            markup=False,
                            size_hint_y=None,
                        )
                    )

                # авто-высота карточки (примерно)
                card.bind(minimum_height=card.setter("height"))
                card.height = dp(10)  # стартовая, дальше Kivy разрулит через минимум у детей
                col.add_widget(card)

            scroll.add_widget(col)
            root.add_widget(scroll)
            self.add_widget(root)
            return

        # ---- MODE 2: section -> topics
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
            lst = MDList(spacing=dp(10), padding=[0, dp(6), 0, dp(6)])

            for t in topics:
                item = MDListItem(
                    on_release=lambda _w, tid=t.id, tt=t.title: app.open_topic(int(tid), str(tt))
                )
                headline = MDListItemHeadlineText(text=str(t.title))
                item.add_widget(headline)
                self._style_list_item(item, headline, None)
                lst.add_widget(item)

            scroll.add_widget(lst)
            root.add_widget(scroll)
            self.add_widget(root)
            return

        # ---- MODE 3: course -> sections
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
        lst = MDList(spacing=dp(10), padding=[0, dp(6), 0, dp(6)])

        for s in sections:
            item = MDListItem(
                on_release=lambda _w, sid=s.id, stt=s.title: app.open_section(int(sid), str(stt))
            )
            headline = MDListItemHeadlineText(text=str(s.title))
            item.add_widget(headline)
            self._style_list_item(item, headline, None)
            lst.add_widget(item)

        scroll.add_widget(lst)
        root.add_widget(scroll)
        self.add_widget(root)
