# /home/ulyashka_88/molecule-mentor/screens/ai_assistant_screen.py
from __future__ import annotations

import logging
from typing import Optional

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField

from utils.textfield_colors import harden_mdtextfield_colors
from .base_screen import BaseScreen

log = logging.getLogger(__name__)


class AIAssistantScreen(BaseScreen):
    _send_text: Optional[MDButtonText] = None

    def on_pre_enter(self, *args):
        self.title = "ИИ-помощник"
        super().on_pre_enter(*args)
        Clock.schedule_once(lambda *_: self._render(), 0)

    def _render(self):
        app = self.get_app()
        self.clear_widgets()

        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        # --- messages area
        self._scroll = MDScrollView(do_scroll_x=False)

        self._messages = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(10),
            padding=(0, 0),
        )
        self._messages.bind(minimum_height=self._messages.setter("height"))
        self._scroll.add_widget(self._messages)

        root.add_widget(self._scroll)

        # --- input row
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(10))

        self._input = MDTextField(
            hint_text="Вопрос",
            mode="filled",
            size_hint_x=0.78,
            size_hint_y=None,
            height=dp(44),
        )

        # Фикс цвета ввода (KivyMD 2.x любит "откатывать" цвет текста)
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

    # ---------------- UI helpers ----------------

    def _make_bubble(self, role: str, text: str) -> MDCard:
        # Цвет текста — всегда читаемый
        text_main = (1, 1, 1, 1)

        # Тёмные bubble, разные для user / ai
        if role == "user":
            card_bg = (0.18, 0.20, 0.30, 1)   # тёмно-синий
        else:
            card_bg = (0.14, 0.16, 0.22, 1)   # ещё темнее для ИИ

        prefix = "Ты: " if role == "user" else "ИИ: "

        card = MDCard(
            md_bg_color=card_bg,
            theme_bg_color="Custom",  # ✅ критично, иначе может подхватывать светлую тему
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

        # чтобы текст корректно переносился и карточка подстраивалась по высоте
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
            self._scroll.scroll_y = 0  # низ
        except Exception:
            pass

    # ---------------- state ----------------

    def _sync_history(self, scroll_to_bottom: bool = False):
        app = self.get_app()
        if not hasattr(app, "ai_history"):
            app.ai_history = []

        self._messages.clear_widgets()

        for role, text in app.ai_history:
            self._messages.add_widget(self._make_bubble(role, text))

        if scroll_to_bottom:
            Clock.schedule_once(lambda *_: self._scroll_to_bottom(), 0)

    # ---------------- actions ----------------

    def _send_message(self):
        app = self.get_app()
        text = (self._input.text or "").strip()
        if not text:
            return

        self._input.text = ""
        self._send.disabled = True

        if not hasattr(app, "ai_history"):
            app.ai_history = []

        # 1) Добавляем в историю для UI
        app.ai_history.append(("user", text))
        app.ai_history.append(("assistant", "Думаю..."))
        self._sync_history(scroll_to_bottom=True)

        engine = getattr(app, "_ai_engine", None)
        if not engine:
            app.ai_history[-1] = ("assistant", "AI engine not ready")
            self._sync_history(scroll_to_bottom=True)
            self._send.disabled = False
            return

        # 2) В движок отправляем ИСТОРИЮ ДО текущего сообщения (чтобы вопрос не дублировался)
        # Последние два элемента сейчас: ("user", text), ("assistant","Думаю...")
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

            # заменяем последнюю "Думаю..." на реальный ответ
            if app.ai_history and app.ai_history[-1] == ("assistant", "Думаю..."):
                app.ai_history[-1] = ("assistant", ans)
            else:
                app.ai_history.append(("assistant", ans))

            Clock.schedule_once(lambda *_: self._after_answer(), 0)

        fut.add_done_callback(_on_done)

    def _after_answer(self):
        self._sync_history(scroll_to_bottom=True)
        self._send.disabled = False
