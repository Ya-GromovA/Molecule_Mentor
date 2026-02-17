from __future__ import annotations

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.graphics import Color, Line, Rectangle
from kivy.uix.boxlayout import BoxLayout

from kivymd.uix.card import MDCard
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView

from utils.reaction_repo import ReactionRepo
from .base_screen import BaseScreen

from typing import Optional


class ReactionCard(MDCard):
    """Карточка реакции."""

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


        self._tap_uid = None
        self._tap_start = (0.0, 0.0)
        self._tap_moved = False

    @staticmethod
    def _make_pressed(rgba, delta: float):
        r, g, b, a = rgba
        return [min(1.0, r + delta), min(1.0, g + delta), min(1.0, b + delta), a]

    def _update_border(self, *_):
        self._border_line.rounded_rectangle = [self.x, self.y, self.width, self.height, 18]

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):

            self.md_bg_color = self._pressed_bg
            self._tap_uid = getattr(touch, "uid", None)
            self._tap_start = tuple(touch.pos)
            self._tap_moved = False
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._tap_uid is not None and getattr(touch, "uid", None) == self._tap_uid:
            dx = float(touch.x - self._tap_start[0])
            dy = float(touch.y - self._tap_start[1])
            if (dx * dx + dy * dy) ** 0.5 > dp(12):
                self._tap_moved = True
                self.md_bg_color = self._normal_bg
            grab = getattr(touch, "grab_current", None)
            if grab is not None and grab is not self:
                self._tap_moved = True
                self.md_bg_color = self._normal_bg
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        uid = getattr(touch, "uid", None)
        is_our_tap = self._tap_uid is not None and uid == self._tap_uid

        was_inside = self.collide_point(*touch.pos)
        self.md_bg_color = self._normal_bg
        self._tap_uid = None

        if is_our_tap and (not self._tap_moved) and was_inside and self._on_open:
            try:
                self._on_open()
            except Exception as e:
                Logger.exception(f"[ReactionCard] open failed: {e}")
            return True

        return super().on_touch_up(touch)


class ReactionsScreen(BaseScreen):
    """Список реакций."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._all_items: list[dict] = []
        self._active_filter = "all"
        self._cards_box: Optional[BoxLayout] = None

    def on_pre_enter(self, *args):
        self.title = "Реакции"
        super().on_pre_enter(*args)
        Clock.schedule_once(lambda *_: self._load(), 0)

    def set_filter(self, key: str) -> None:
        k = (key or "all").strip().lower()
        if k not in {"all", "organic", "inorganic", "bio", "fav"}:
            k = "all"
        self._active_filter = k
        self._sync_filter_buttons()
        self._render_items()

    def _sync_filter_buttons(self) -> None:
        ids = getattr(self, "ids", {}) or {}
        btns = {
            "all": ids.get("rxn_filter_all"),
            "organic": ids.get("rxn_filter_organic"),
            "inorganic": ids.get("rxn_filter_inorganic"),
            "bio": ids.get("rxn_filter_bio"),
            "fav": ids.get("rxn_filter_fav"),
        }
        app = self.get_app()
        active_bg = getattr(app, "mm_primary", (0.22, 0.87, 0.80, 1.0))
        inactive_bg = getattr(app, "mm_surface2", (0.13, 0.16, 0.24, 1.0))
        active_text = (0, 0, 0, 1)
        inactive_text = getattr(app, "mm_text", (1, 1, 1, 1))

        for k, b in btns.items():
            if not b:
                continue
            is_active = k == self._active_filter
            try:
                b.theme_bg_color = "Custom"
                b.md_bg_color = active_bg if is_active else inactive_bg
            except Exception:
                pass
            try:
                for ch in getattr(b, "children", []) or []:
                    if getattr(ch, "__class__", None) and ch.__class__.__name__ == "MDButtonText":
                        ch.theme_text_color = "Custom"
                        ch.text_color = active_text if is_active else inactive_text
            except Exception:
                pass

    @staticmethod
    def _kind_from_category(cat: str) -> str:
        c = (cat or "").strip().lower()
        if c.startswith("орган"):
            return "organic"
        if c.startswith("неорган"):
            return "inorganic"
        if c.startswith("био"):
            return "bio"
        return "other"

    def _favorites_path(self) -> str:
        try:
            from pathlib import Path
            app = self.get_app()
            return str(Path(app.user_data_dir).resolve() / "favorites.json")
        except Exception:
            return "favorites.json"

    def _favorite_ids(self) -> set[str]:
        try:
            from utils.favorites_store import load_favorites
            fav = load_favorites(self._favorites_path())
            return set(fav.reactions)
        except Exception:
            return set()

    def _load(self):
        app = self.get_app()
        self.clear_widgets()

        repo = ReactionRepo(app.reactions_dir)
        items = repo.list_reactions()
        self._all_items = list(items)


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


        filters_scroll = MDScrollView(
            do_scroll_y=False,
            do_scroll_x=True,
            size_hint_y=None,
            height=dp(42),
            bar_width=0,
        )
        filters_row = BoxLayout(orientation="horizontal", size_hint=(None, None), height=dp(42), spacing=dp(8))
        filters_row.bind(minimum_width=filters_row.setter("width"))
        filters_scroll.add_widget(filters_row)
        root.add_widget(filters_scroll)

        def _mk_btn(btn_id: str, text: str, key: str, w: int):
            b = MDButton(
                style="filled",
                size_hint=(None, None),
                width=dp(w),
                height=dp(34),
                radius=[dp(16)] * 4,
            )
            b.add_widget(MDButtonText(text=text))
            b.bind(on_release=lambda *_: self.set_filter(key))
            try:
                self.ids[btn_id] = b
            except Exception:
                pass
            return b

        filters_row.add_widget(_mk_btn("rxn_filter_all", "Все", "all", 86))
        filters_row.add_widget(_mk_btn("rxn_filter_organic", "Органика", "organic", 120))
        filters_row.add_widget(_mk_btn("rxn_filter_inorganic", "Неорганика", "inorganic", 132))
        filters_row.add_widget(_mk_btn("rxn_filter_bio", "Биохимия", "bio", 118))
        filters_row.add_widget(_mk_btn("rxn_filter_fav", "Избранное", "fav", 142))

        self._sync_filter_buttons()

        scroll = MDScrollView(do_scroll_x=False, bar_width=dp(6))
        cards = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(getattr(app, "mm_molecules_list_spacing", 10)),
            padding=(0, 0, 0, dp(getattr(app, "mm_molecules_list_bottom_padding", 10))),
        )
        cards.bind(minimum_height=cards.setter("height"))
        scroll.add_widget(cards)

        self._cards_box = cards

        root.add_widget(scroll)
        self.add_widget(root)

        self._render_items()

    def _render_items(self) -> None:
        app = self.get_app()
        cards = self._cards_box
        if not cards:
            return

        cards.clear_widgets()
        fav_ids = self._favorite_ids()

        def allow(it: dict) -> bool:
            if self._active_filter == "fav":
                return str(it.get("reaction_id") or "") in fav_ids
            if self._active_filter == "all":
                return True
            kind = self._kind_from_category(str(it.get("category") or ""))
            return kind == self._active_filter

        items = [it for it in (self._all_items or []) if allow(it)]

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

        for idx, it in enumerate(items):
            rid = str(it.get("reaction_id") or "")
            name = str(it.get("name") or rid).strip() or rid
            eq = str(it.get("equation") or "").strip()
            cat = str(it.get("category") or "").strip()
            kind = self._kind_from_category(cat)
            prefix = ""
            if kind == "organic":
                prefix = "Органика"
            elif kind == "inorganic":
                prefix = "Неорганика"
            elif kind == "bio":
                prefix = "Биохимия"

            eq_line = eq
            if prefix:
                eq_line = f"{prefix} | {eq}".strip()

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

            if idx < 12:
                card.opacity = 0
                delay = 0.035 * idx
                Clock.schedule_once(
                    lambda _dt, c=card: Animation(opacity=1, d=0.30, t="out_cubic").start(c),
                    delay,
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
                text=eq_line,
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
                while lbl.texture_size[0] > content_w and lbl.font_size > min_fs:
                    lbl.font_size = lbl.font_size - dp(1)
                    lbl.texture_update()

            def _reflow_card(card_ref=card, lbl_eq_ref=lbl_eq, adjust_fn=_adjust_title_font, *_):
                content_w = max(dp(100), card_ref.width - dp(24))
                lbl_eq_ref.text_size = (content_w, None)
                adjust_fn()

            card.bind(size=_reflow_card)
            Clock.schedule_once(lambda dt, fn=_reflow_card: fn(), 0)
