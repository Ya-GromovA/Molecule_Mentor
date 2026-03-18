from __future__ import annotations

from pathlib import Path
from typing import Optional

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView

from utils.favorites_store import load_favorites
from utils.reaction_repo import ReactionRepo

from .base_screen import BaseScreen


class _TapCard(MDCard):
    def __init__(self, on_open=None, pressed_delta=0.08, **kwargs):
        super().__init__(**kwargs)
        self._on_open = on_open
        self._normal_bg = list(getattr(self, "md_bg_color", (0.10, 0.11, 0.14, 1)))
        self._pressed_bg = [
            min(1.0, self._normal_bg[0] + pressed_delta),
            min(1.0, self._normal_bg[1] + pressed_delta),
            min(1.0, self._normal_bg[2] + pressed_delta),
            self._normal_bg[3],
        ]
        self._tap_uid = None
        self._tap_start = (0.0, 0.0)
        self._tap_moved = False

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
            except Exception:
                Logger.exception("[Favorites] open failed")
            return True
        return super().on_touch_up(touch)


class FavoritesScreen(BaseScreen):
    """Избранное: молекулы и реакции."""
    def on_pre_enter(self, *args):
        self.title = "Избранное"
        super().on_pre_enter(*args)
        Clock.schedule_once(lambda *_: self._load(), 0)

    def _favorites_path(self) -> str:
        app = self.get_app()
        return str(Path(app.user_data_dir).resolve() / "favorites.json")

    def _assets_molecules_dir(self) -> Path:
        project_root = Path(__file__).resolve().parents[1]
        return project_root / "assets" / "molecules"

    def _load(self) -> None:
        app = self.get_app()
        self.clear_widgets()

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))
        with root.canvas.before:
            Color(*getattr(app, "mm_bg", (0.06, 0.07, 0.09, 1)))
            self._bg_rect = RoundedRectangle(pos=root.pos, size=root.size, radius=[dp(0)])
        root.bind(pos=lambda *_: setattr(self._bg_rect, "pos", root.pos), size=lambda *_: setattr(self._bg_rect, "size", root.size))

        fav = load_favorites(self._favorites_path())

        scroll = MDScrollView(do_scroll_x=False, bar_width=dp(6))
        col = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10), padding=(0, 0, 0, dp(16)))
        col.bind(minimum_height=col.setter("height"))
        scroll.add_widget(col)
        root.add_widget(scroll)
        self.add_widget(root)

        text1 = getattr(app, "mm_text", (1, 1, 1, 1))
        text2 = getattr(app, "mm_text2", (0.75, 0.78, 0.85, 1))
        card_bg = getattr(app, "mm_molecules_card_bg", (0.10, 0.11, 0.14, 1))

        def header(title: str):
            col.add_widget(
                MDLabel(
                    text=title,
                    bold=True,
                    theme_text_color="Custom",
                    text_color=text1,
                    font_size=dp(16),
                    size_hint_y=None,
                    height=dp(26),
                )
            )


        header("Молекулы")
        mol_dir = self._assets_molecules_dir()

        try:
            from screens.molecules_screen import _MOLECULE_DATA
            from utils.molecule_db import resolve_name_formula
        except Exception:
            _MOLECULE_DATA = {}
            resolve_name_formula = None

        mol_keys = sorted(fav.molecules)
        if not mol_keys:
            col.add_widget(
                MDLabel(
                    text="Пока нет избранных молекул",
                    theme_text_color="Custom",
                    text_color=text2,
                    size_hint_y=None,
                    height=dp(22),
                )
            )
        else:
            for k in mol_keys:
                pdb = mol_dir / f"{k}.pdb"
                if not pdb.exists():
                    continue
                if callable(resolve_name_formula):
                    ru, formula = resolve_name_formula(key=str(k), pdb_path=pdb)
                else:
                    ru, formula = str(k), ""
                desc = str(_MOLECULE_DATA.get(k, ("", ""))[1] or "")

                title_line = f"{ru} ({formula})" if formula else ru

                def _open_molecule(
                    p=str(pdb),
                    ttl=title_line,
                    d=desc,
                    key=str(k),
                    ru_label=str(ru),
                    frm=str(formula),
                ):
                    app.open_molecule_viewer(p, ttl, d, molecule_key=key, ru_name=ru_label, formula=frm)

                card = _TapCard(
                    on_open=_open_molecule,
                    md_bg_color=list(card_bg),
                    theme_bg_color="Custom",
                    radius=[18, 18, 18, 18],
                    padding=(dp(16), dp(12), dp(16), dp(12)),
                    size_hint_x=1,
                    size_hint_y=None,
                    height=dp(66),
                )
                box = BoxLayout(orientation="vertical", spacing=dp(2))
                box.add_widget(
                    MDLabel(
                        text=title_line,
                        bold=True,
                        theme_text_color="Custom",
                        text_color=text1,
                        font_size=dp(16),
                        shorten=True,
                        shorten_from="right",
                        max_lines=1,
                        size_hint_y=None,
                        height=dp(24),
                    )
                )
                box.add_widget(
                    MDLabel(
                        text=k,
                        theme_text_color="Custom",
                        text_color=text2,
                        font_size=dp(12),
                        shorten=True,
                        shorten_from="right",
                        max_lines=1,
                        size_hint_y=None,
                        height=dp(18),
                    )
                )
                card.add_widget(box)
                col.add_widget(card)


        header("Реакции")
        rxn_ids = sorted(fav.reactions)
        if not rxn_ids:
            col.add_widget(
                MDLabel(
                    text="Пока нет избранных реакций",
                    theme_text_color="Custom",
                    text_color=text2,
                    size_hint_y=None,
                    height=dp(22),
                )
            )
        else:
            repo = ReactionRepo(app.reactions_dir)
            items = {str(it.get("reaction_id") or ""): it for it in repo.list_reactions()}
            for rid in rxn_ids:
                it = items.get(rid)
                if not it:
                    continue
                name = str(it.get("name") or rid)
                eq = str(it.get("equation") or "")

                def _open_reaction(reaction_id=str(rid), title=str(name)):
                    app.open_reaction_viewer(reaction_id, title)

                card = _TapCard(
                    on_open=_open_reaction,
                    md_bg_color=list(card_bg),
                    theme_bg_color="Custom",
                    radius=[18, 18, 18, 18],
                    padding=(dp(16), dp(12), dp(16), dp(12)),
                    size_hint_x=1,
                    size_hint_y=None,
                    height=dp(66),
                )
                box = BoxLayout(orientation="vertical", spacing=dp(2))
                box.add_widget(
                    MDLabel(
                        text=name,
                        bold=True,
                        theme_text_color="Custom",
                        text_color=text1,
                        font_size=dp(16),
                        shorten=True,
                        shorten_from="right",
                        max_lines=1,
                        size_hint_y=None,
                        height=dp(24),
                    )
                )
                box.add_widget(
                    MDLabel(
                        text=eq,
                        theme_text_color="Custom",
                        text_color=text2,
                        font_size=dp(12),
                        shorten=True,
                        shorten_from="right",
                        max_lines=1,
                        size_hint_y=None,
                        height=dp(18),
                    )
                )
                card.add_widget(box)
                col.add_widget(card)
