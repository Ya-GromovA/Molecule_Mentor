from __future__ import annotations

from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen


class BaseScreen(Screen):
    title = StringProperty("")

    def get_app(self):
        from kivy.app import App
        return App.get_running_app()

    def on_pre_enter(self, *args):
        app = self.get_app()
        if self.title:
            app.set_top_title(self.title)
        app.set_back_visible(self.name != "home")

    def go_back(self):
        self.get_app().go_back()
