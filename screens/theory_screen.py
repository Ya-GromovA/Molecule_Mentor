
from __future__ import annotations

import re
from pathlib import Path

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView

from kivymd.uix.label import MDLabel

from .base_screen import BaseScreen


def sanitize_text(text: str) -> str:
    """Убирает нечитаемые символы и Markdown из текста."""
    if not text:
        return ""

    # убираем куски LaTeX
    text = text.replace("\\[", "")
    text = text.replace("\\]", "")
    text = text.replace("\\(", "")
    text = text.replace("\\)", "")
    text = text.replace("\\rightarrow", "->")
    text = text.replace("\\leftarrow", "<-")
    text = text.replace("\\leftrightarrow", "<->")
    text = text.replace("\\rightleftharpoons", "<->")
    text = text.replace("\\leftrightharpoons", "<->")
    text = re.sub(r"\\text\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\^\{([^}]*)\}", r"^\1", text)
    text = re.sub(r"_\{([^}]*)\}", r"_\1", text)
    text = text.replace("\\", "")
    
    # заменяем греческие буквы
    text = text.replace("σ", "сигма")
    text = text.replace("π", "пи")
    text = text.replace("α", "альфа")
    text = text.replace("β", "бета")
    text = text.replace("γ", "гамма")
    text = text.replace("δ", "дельта")
    
    # заменяем спецсимволы
    text = text.replace("→", "->")
    text = text.replace("←", "<-")
    text = text.replace("↔", "<->")
    text = text.replace("≡", "=")
    text = text.replace("≠", "!=")
    text = text.replace("≤", "<=")
    text = text.replace("≥", ">=")
    text = text.replace("±", "+/-")
    text = text.replace("°", " градусов")
    text = text.replace("−", "-")
    text = text.replace("–", "-")
    text = text.replace("—", " - ")
    text = text.replace("…", "...")
    text = text.replace("«", "\"")
    text = text.replace("»", "\"")
    text = text.replace("'", "'")
    text = text.replace("'", "'")
    text = text.replace(""", "\"")
    text = text.replace(""", "\"")
    
    # убираем Markdown разметку
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold** -> bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)       # *italic* -> italic
    text = re.sub(r'__([^_]+)__', r'\1', text)       # __bold__ -> bold
    text = re.sub(r'_([^_]+)_', r'\1', text)         # _italic_ -> italic
    text = re.sub(r'`([^`]+)`', r'\1', text)         # `code` -> code
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)  # # headers
    
    return text


class TheoryCard(BoxLayout):
    """Тёмная карточка для контента теории."""

    def __init__(self, bg_color=(0.08, 0.10, 0.16, 1), **kwargs):
        super().__init__(**kwargs)
        self._bg_color = bg_color

        with self.canvas.before:
            Color(*self._bg_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[18, 18, 18, 18])

        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size


class TheoryScreen(BaseScreen):
    """
    Экран отображения теории (блоков контента) для выбранной темы.
    
    nav_state:
      - topic_id: int
      - topic_title: str
    """

    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        Clock.schedule_once(lambda *_: self._render(), 0)

    def _content_base_dir(self) -> Path:
        """База для относительных путей в topic_blocks.content."""
        app = self.get_app()
        try:
            db_path = Path(app.courses_db)
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

    def _render(self):
        app = self.get_app()
        repo = app.course_repo
        st = dict(getattr(app, "nav_state", {}) or {})

        topic_id = st.get("topic_id")
        topic_title = st.get("topic_title") or "Тема"

        self.clear_widgets()

        # фон
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        bg_rgba = getattr(app, "mm_bg", (0.12, 0.15, 0.25, 1))
        with root.canvas.before:
            Color(*bg_rgba)
            self._bg_rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_bg, size=self._update_bg)

        # заголовок
        self.title = str(topic_title)
        app.set_top_title(self.title)

        if topic_id is None:
            root.add_widget(
                MDLabel(
                    text="Тема не выбрана",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=app.mm_text2,
                )
            )
            self.add_widget(root)
            return

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

        scroll = ScrollView(do_scroll_x=False)
        col = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10), padding=(0, 0))
        col.bind(minimum_height=col.setter("height"))

        for b in blocks:
            card = TheoryCard(
                bg_color=(0.08, 0.10, 0.16, 1),
                orientation="vertical",
                size_hint_y=None,
                padding=[dp(14), dp(14), dp(14), dp(14)],
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
                            text=sanitize_text(str(b.caption)),
                            theme_text_color="Custom",
                            text_color=app.mm_text2,
                            size_hint_y=None,
                        )
                    )
            else:
                # текст по умолчанию
                clean_text = sanitize_text(str(b.content or "").strip())
                lbl = MDLabel(
                    text=clean_text,
                    theme_text_color="Custom",
                    text_color=app.mm_text,
                    markup=False,
                    size_hint_y=None,
                )
                lbl.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
                card.add_widget(lbl)

            card.bind(minimum_height=card.setter("height"))
            col.add_widget(card)

        scroll.add_widget(col)
        root.add_widget(scroll)
        self.add_widget(root)

    def _update_bg(self, instance, *_):
        if hasattr(self, "_bg_rect"):
            self._bg_rect.pos = instance.pos
            self._bg_rect.size = instance.size
