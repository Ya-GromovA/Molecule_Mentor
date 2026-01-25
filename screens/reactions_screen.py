from __future__ import annotations

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.graphics import Color, Line, Rectangle
from kivy.uix.boxlayout import BoxLayout

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView

from utils.reaction_repo import ReactionRepo
from .base_screen import BaseScreen


class ReactionCard(MDCard):
    """
    Карточка реакции в стиле экрана Молекулы:
    - без ButtonBehavior/RectangularRippleBehavior (не ловим MRO)
    - "нажатие" руками
    - тонкая рамка через canvas.after
    """

    def __init__(self, on_open=None, border_rgba=(1, 1, 1, 0.16), pressed_delta=0.08, **kwargs):
        super().__init__(**kwargs)
        self._on_open = on_open

        self._normal_bg = list(getattr(self, "md_bg_color", (0.10, 0.11, 0.14, 1)))
        self._pressed_bg = self._make_pressed(self._normal_bg, pressed_delta)

        with self.canvas.after:
            self._border_color = Color(*border_rgba)
            self._border_line = Line(
                rounded_rectangle=[self.x, self.y, self.width, self.height, 18],
                width=1,
            )
        self.bind(pos=self._update_border, size=self._update_border)

    @staticmethod
    def _make_pressed(rgba, delta: float):
        r, g, b, a = rgba
        return [min(1.0, r + delta), min(1.0, g + delta), min(1.0, b + delta), a]

    def _update_border(self, *_):
        self._border_line.rounded_rectangle = [self.x, self.y, self.width, self.height, 18]

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.md_bg_color = self._pressed_bg
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        was_inside = self.collide_point(*touch.pos)
        self.md_bg_color = self._normal_bg
        if was_inside and self._on_open:
            try:
                self._on_open()
            except Exception as e:
                Logger.exception(f"[ReactionCard] open failed: {e}")
            return True
        return super().on_touch_up(touch)


class ReactionsScreen(BaseScreen):
    def on_pre_enter(self, *args):
        self.title = "Реакции"
        super().on_pre_enter(*args)
        Clock.schedule_once(lambda *_: self._load(), 0)

    def _load(self):
        app = self.get_app()
        self.clear_widgets()

        repo = ReactionRepo(app.reactions_dir)
        items = repo.list_reactions()

        # root with dark background like Molecules screen
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))

        bg_rgba = getattr(app, "mm_bg", None) or getattr(app, "mm_surface", None) or (0.06, 0.07, 0.09, 1)
        with root.canvas.before:
            self._bg_color = Color(*bg_rgba)
            self._bg_rect = Rectangle(pos=root.pos, size=root.size)

        def _upd_bg(*_):
            self._bg_rect.pos = root.pos
            self._bg_rect.size = root.size

        root.bind(pos=_upd_bg, size=_upd_bg)

        if not items:
            root.add_widget(
                MDLabel(
                    text="Реакции не найдены",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=getattr(app, "mm_text", (1, 1, 1, 1)),
                )
            )
            self.add_widget(root)
            return

        scroll = MDScrollView(do_scroll_x=False, bar_width=dp(6))
        cards = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(getattr(app, "mm_molecules_list_spacing", 10)),
            padding=(0, 0, 0, dp(getattr(app, "mm_molecules_list_bottom_padding", 10))),
        )
        cards.bind(minimum_height=cards.setter("height"))
        scroll.add_widget(cards)

        root.add_widget(scroll)
        self.add_widget(root)

        # styles like molecule cards
        card_bg = getattr(app, "mm_molecules_card_bg", (0.10, 0.11, 0.14, 1))
        border = getattr(app, "mm_molecules_card_border", (1, 1, 1, 0.16))
        pressed_delta = float(getattr(app, "mm_molecules_card_pressed_delta", 0.08))
        elevation = int(getattr(app, "mm_molecules_card_elevation", 1))

        text1 = getattr(app, "mm_text", (1, 1, 1, 1))
        text2 = getattr(app, "mm_text2", (0.75, 0.78, 0.85, 1))

        title_fs_base = dp(18)
        title_fs_min = dp(12)
        sub_fs = dp(13)
        card_height_fixed = dp(64)

        for it in items:
            rid = str(it.get("reaction_id") or "")
            name = str(it.get("name") or rid).strip() or rid
            eq = str(it.get("equation") or "").strip()

            def _open(reaction_id=rid, title=name):
                app.open_reaction_viewer(reaction_id, title)

            card = ReactionCard(
                on_open=_open,
                md_bg_color=list(card_bg),
                theme_bg_color="Custom",
                border_rgba=border,
                pressed_delta=pressed_delta,
                elevation=elevation,
                radius=[14, 14, 14, 14],
                padding=(dp(12), dp(8), dp(12), dp(8)),
                size_hint_x=1,
                size_hint_y=None,
                height=card_height_fixed,
            )

            box = BoxLayout(orientation="vertical", spacing=dp(2), size_hint_y=None)
            box.height = card_height_fixed - dp(16)

            lbl_title = MDLabel(
                text=name,
                bold=True,
                theme_text_color="Custom",
                text_color=text1,
                font_size=title_fs_base,
                halign="left",
                valign="middle",
                shorten=True,
                shorten_from="right",
                max_lines=1,
                size_hint_y=None,
                height=dp(24),
            )
            lbl_eq = MDLabel(
                text=eq,
                theme_text_color="Custom",
                text_color=text2,
                font_size=sub_fs,
                halign="left",
                valign="middle",
                shorten=True,
                shorten_from="right",
                max_lines=1,
                size_hint_y=None,
                height=dp(18),
            )

            box.add_widget(lbl_title)
            box.add_widget(lbl_eq)
            card.add_widget(box)
            cards.add_widget(card)

            def _adjust_title_font(lbl=lbl_title, base_fs=title_fs_base, min_fs=title_fs_min, card_ref=card):
                content_w = max(dp(100), card_ref.width - dp(24))
                lbl.text_size = (content_w, None)
                lbl.font_size = base_fs
                lbl.texture_update()
                # Уменьшаем шрифт если текст не помещается
                while lbl.texture_size[0] > content_w and lbl.font_size > min_fs:
                    lbl.font_size = lbl.font_size - dp(1)
                    lbl.texture_update()

            def _reflow_card(card_ref=card, lbl_title_ref=lbl_title, lbl_eq_ref=lbl_eq, adjust_fn=_adjust_title_font, *_):
                content_w = max(dp(100), card_ref.width - dp(24))
                lbl_eq_ref.text_size = (content_w, None)
                adjust_fn()

            card.bind(size=_reflow_card)
            Clock.schedule_once(lambda dt, fn=_reflow_card: fn(), 0)
