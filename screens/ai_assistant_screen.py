
from __future__ import annotations

import logging
from typing import Optional

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout

from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField

from utils.textfield_colors import harden_mdtextfield_colors
from .base_screen import BaseScreen

log = logging.getLogger(__name__)


class AIAssistantScreen(BaseScreen):
    """Чат с помощником по химии."""
    _send_text: Optional[MDButtonText] = None
    _prev_softinput_mode: Optional[str] = None
    _base_padding: float = 0
    _root: Optional[FloatLayout] = None
    _content: Optional[BoxLayout] = None
    _input_row: Optional[BoxLayout] = None
    _keyboard_ev = None
    _last_keyboard_height: int = 0
    _row_height: float = 0

    def on_pre_enter(self, *args):
        self.title = "ИИ-помощник"
        super().on_pre_enter(*args)
        self._prev_softinput_mode = getattr(Window, "softinput_mode", None)
        try:
            Window.softinput_mode = "pan"
        except Exception:
            pass
        try:
            Window.bind(on_keyboard_height=self._on_keyboard_height)
        except Exception:
            pass
        Clock.schedule_once(lambda *_: self._render(), 0)

    def on_pre_leave(self, *args):
        if self._prev_softinput_mode is not None:
            try:
                Window.softinput_mode = self._prev_softinput_mode
            except Exception:
                pass
        try:
            Window.unbind(on_keyboard_height=self._on_keyboard_height)
        except Exception:
            pass
        if self._keyboard_ev is not None:
            try:
                self._keyboard_ev.cancel()
            except Exception:
                pass
            self._keyboard_ev = None
        return super().on_pre_leave(*args)

    def _render(self):
        app = self.get_app()
        self.clear_widgets()

        self._base_padding = dp(10)
        self._row_height = dp(44)
        root = FloatLayout()
        self._root = root

        content = BoxLayout(
            orientation="vertical",
            padding=[self._base_padding, self._base_padding, self._base_padding, self._base_padding + self._row_height],
            spacing=dp(10),
            size_hint=(1, 1),
        )
        self._content = content


        self._scroll = MDScrollView(do_scroll_x=False)

        self._messages = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(10),
            padding=(0, 0),
        )
        self._messages.bind(minimum_height=self._messages.setter("height"))
        self._scroll.add_widget(self._messages)

        content.add_widget(self._scroll)
        root.add_widget(content)


        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=self._row_height, spacing=dp(10))
        row.size_hint = (1, None)
        row.pos_hint = {"x": 0, "y": 0}
        self._input_row = row

        self._input = MDTextField(
            hint_text="Вопрос",
            mode="filled",
            size_hint_x=0.78,
            size_hint_y=None,
            height=dp(44),
            multiline=False,
        )
        try:
            self._input.input_type = "text"
            self._input.keyboard_suggestions = True
            self._input.write_tab = False
        except Exception:
            pass


        harden_mdtextfield_colors(
            self._input,
            text_rgba=tuple(getattr(app, "mm_text", (1, 1, 1, 1))),
        )

        self._send = MDButton(
            style="filled",
            on_release=lambda *_: self._send_message(),
        )
        self._send_text = MDButtonText(text="Отправить")
        self._send.add_widget(self._send_text)

        row.add_widget(self._input)
        row.add_widget(self._send)
        root.add_widget(row)

        self.add_widget(root)
        self._sync_history(scroll_to_bottom=True)
        if self._keyboard_ev is None:
            self._keyboard_ev = Clock.schedule_interval(self._refresh_keyboard_offset, 0.1)

    def _apply_keyboard_offset(self, height: int) -> None:
        if not self._root:
            return
        extra = max(0, int(height or 0))
        if self._input_row:
            self._input_row.y = extra
        if self._content:
            base = self._base_padding
            self._content.padding = [base, base, base, base + self._row_height + extra]

    def _on_keyboard_height(self, _window, height: int) -> None:
        self._last_keyboard_height = int(height or 0)
        self._apply_keyboard_offset(self._last_keyboard_height)

    def _refresh_keyboard_offset(self, _dt) -> None:
        height = int(getattr(Window, "keyboard_height", 0) or 0)
        if height != self._last_keyboard_height:
            self._last_keyboard_height = height
            self._apply_keyboard_offset(height)



    def _make_bubble(self, role: str, text: str) -> MDCard:

        text_main = (1, 1, 1, 1)


        if role == "user":
            card_bg = (0.18, 0.20, 0.30, 1)
        else:
            card_bg = (0.14, 0.16, 0.22, 1)

        prefix = "Ты: " if role == "user" else "ИИ: "

        card = MDCard(
            md_bg_color=card_bg,
            theme_bg_color="Custom",
            radius=[dp(14)] * 4,
            padding=(dp(12), dp(10), dp(12), dp(10)),
            size_hint_x=1,
            size_hint_y=None,
        )

        lbl = MDLabel(
            text=f"{prefix}{text}",
            theme_text_color="Custom",
            text_color=text_main,
            halign="left",
            valign="top",
            size_hint_y=None,
        )


        def _reflow(*_):
            lbl.text_size = (card.width - dp(24), None)
            lbl.texture_update()
            lbl.height = max(dp(24), lbl.texture_size[1])
            card.height = lbl.height + dp(20)

        card.bind(width=_reflow)
        _reflow()

        card.add_widget(lbl)
        return card

    def _scroll_to_bottom(self):
        try:
            self._scroll.scroll_y = 0
        except Exception:
            pass



    def _sync_history(self, scroll_to_bottom: bool = False):
        app = self.get_app()
        if not hasattr(app, "ai_history"):
            app.ai_history = []

        self._messages.clear_widgets()

        for role, text in app.ai_history:
            self._messages.add_widget(self._make_bubble(role, text))

        if scroll_to_bottom:
            Clock.schedule_once(lambda *_: self._scroll_to_bottom(), 0)



    def _send_message(self):
        app = self.get_app()
        text = (self._input.text or "").strip()
        if not text:
            return

        self._input.text = ""
        self._send.disabled = True

        if not hasattr(app, "ai_history"):
            app.ai_history = []


        app.ai_history.append(("user", text))
        app.ai_history.append(("assistant", "Думаю..."))
        self._sync_history(scroll_to_bottom=True)

        engine = getattr(app, "_ai_engine", None)
        if not engine:
            app.ai_history[-1] = ("assistant", "AI engine not ready")
            self._sync_history(scroll_to_bottom=True)
            self._send.disabled = False
            return



        history_pairs = app.ai_history[:-2]

        history_for_engine = [
            {"role": r, "content": t}
            for r, t in history_pairs
            if t and t != "Думаю..."
        ]

        fut = app._executor.submit(engine.ask, text, history_for_engine)

        def _on_done(_f):
            try:
                ans = _f.result()
            except Exception as e:
                log.exception("AI request failed: %s", e)
                ans = f"Ошибка: {e}"


            if app.ai_history and app.ai_history[-1] == ("assistant", "Думаю..."):
                app.ai_history[-1] = ("assistant", ans)
            else:
                app.ai_history.append(("assistant", ans))

            Clock.schedule_once(lambda *_: self._after_answer(), 0)

        fut.add_done_callback(_on_done)

    def _after_answer(self):
        self._sync_history(scroll_to_bottom=True)
        self._send.disabled = False
