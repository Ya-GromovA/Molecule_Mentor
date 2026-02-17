from __future__ import annotations

from .base_screen import BaseScreen


class HomeScreen(BaseScreen):
    """Главный экран."""
    def on_pre_enter(self, *args):
        self.title = "Главная"
        super().on_pre_enter(*args)
