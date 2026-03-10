from __future__ import annotations

from kivy.clock import Clock
from kivy.properties import NumericProperty, StringProperty

from kivymd.uix.label import MDLabel


class MarqueeLabel(MDLabel):
    full_text = StringProperty("")
    speed = NumericProperty(2.0)
    gap = NumericProperty(8)

    def __init__(self, **kwargs):
        txt = kwargs.pop("text", "")
        super().__init__(**kwargs)
        self.full_text = str(txt)
        self.text = str(txt)
        self._pos = 0.0
        self._ev = Clock.schedule_interval(self._tick, 0.2)
        self.bind(size=lambda *_: self._refresh(), full_text=lambda *_: self._reset(), font_size=lambda *_: self._refresh())
        Clock.schedule_once(lambda *_: self._refresh(), 0)

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self._refresh()

    def on_parent(self, _inst, parent):
        if parent is None and self._ev is not None:
            self._ev.cancel()
            self._ev = None
        elif parent is not None and self._ev is None:
            self._ev = Clock.schedule_interval(self._tick, 0.2)

    def _window_chars(self) -> int:
        try:
            fs = float(self.font_size or 14.0)
        except Exception:
            fs = 14.0
        w = max(40.0, float(self.width or 40.0))
        return max(6, min(120, int(w / max(6.0, fs * 0.62))))

    def _reset(self) -> None:
        self._pos = 0.0
        self._refresh()

    def _refresh(self) -> None:
        title = str(self.full_text or "")
        wnd = self._window_chars()
        if len(title) <= wnd:
            self.text = title
            self._pos = 0.0
            return
        gap = " " * int(self.gap)
        stream = title + gap + title
        cycle = len(title) + len(gap)
        pos = int(self._pos) % cycle
        self.text = stream[pos:pos + wnd]

    def _tick(self, dt: float) -> None:
        title = str(self.full_text or "")
        if not title:
            self.text = ""
            self._pos = 0.0
            return
        wnd = self._window_chars()
        if len(title) <= wnd:
            self.text = title
            self._pos = 0.0
            return
        cycle = len(title) + int(self.gap)
        self._pos += float(dt) * float(self.speed)
        if self._pos >= cycle:
            self._pos = 0.0
        self._refresh()
