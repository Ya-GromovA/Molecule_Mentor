
from __future__ import annotations

from pathlib import Path
from typing import Optional

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import Screen

from kivymd.uix.label import MDLabel

from utils.molecule_parser import MoleculeParseError, parse_pdb
from utils.visualizer_3d import Visualizer3D


class MoleculeViewerScreen(Screen):
    """Просмотр молекулы в 3D."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._viewer: Optional[Visualizer3D] = None
        self._loaded_key: Optional[str] = None
        self._molecule_key: str = ""


    fav_icon = StringProperty("star-outline")

    @property
    def app(self):
        from kivy.app import App
        return App.get_running_app()

    def on_pre_enter(self, *args):

        Clock.schedule_once(lambda *_: self._ensure_ui_and_load(), 0)

    def _ensure_ui_and_load(self) -> None:


        host = self.ids.get("viewer_content_host") or self.ids.get("viewer_host")
        if not host:
            Logger.warning("[MoleculeViewer] KV ids not ready: viewer_host missing")
            return

        nav = getattr(self.app, "nav_state", {}) or {}
        pdb_path = nav.get("pdb_path")
        title = nav.get("title", "Молекула")
        description = nav.get("description", "")

        display_title = str(title or "Молекула")
        try:
            if pdb_path and hasattr(self.app, "_resolve_molecule_title"):
                molecule_key = str(nav.get("molecule_key") or "").strip()
                ru_name = str(nav.get("ru_name") or "").strip()
                formula = str(nav.get("formula") or "").strip()
                display_title = self.app._resolve_molecule_title(
                    str(pdb_path),
                    str(title or ""),
                    molecule_key=molecule_key,
                    ru_name_hint=ru_name,
                    formula_hint=formula,
                )
                nav["title"] = display_title
                self.app.nav_state = nav
        except Exception:
            display_title = str(title or "Молекула")


        try:
            self.app.set_top_title(display_title)
        except Exception:
            pass


        desc_label = self.ids.get("description_label")
        desc_card = self.ids.get("description_card")
        if desc_label and desc_card:
            if description:
                desc_label.text = description
                desc_card.opacity = 1
                desc_card.height = dp(100)
            else:
                desc_label.text = ""
                desc_card.opacity = 0
                desc_card.height = 0

        if not pdb_path:
            self._molecule_key = ""
            self.fav_icon = "star-outline"
            host.clear_widgets()
            host.add_widget(MDLabel(
                text="Нет выбранной молекулы",
                halign="center",
                theme_text_color="Custom",
                text_color=getattr(self.app, "mm_text", (1, 1, 1, 1)),
            ))
            return


        key = str(pdb_path)
        if self._loaded_key == key and self._viewer is not None:
            return
        self._loaded_key = key

        try:
            self._molecule_key = Path(str(pdb_path)).stem
        except Exception:
            self._molecule_key = ""

        self._sync_favorite_icon()

        host.clear_widgets()


        viewer = Visualizer3D()
        self._viewer = viewer
        host.add_widget(viewer)


        try:
            mol = parse_pdb(str(Path(pdb_path)))
            viewer.set_scene(mol.atoms, mol.bonds)
        except MoleculeParseError as e:
            Logger.exception(f"[MoleculeViewer] parse error: {e}")
            host.clear_widgets()
            host.add_widget(MDLabel(
                text=f"Не удалось открыть PDB:\n{e}",
                halign="center",
                theme_text_color="Custom",
                text_color=getattr(self.app, "mm_text", (1, 1, 1, 1)),
            ))
        except Exception as e:
            Logger.exception(f"[MoleculeViewer] failed: {e}")
            host.clear_widgets()
            host.add_widget(MDLabel(
                text=f"Ошибка открытия 3D:\n{e}",
                halign="center",
                theme_text_color="Custom",
                text_color=getattr(self.app, "mm_text", (1, 1, 1, 1)),
            ))

    def _favorites_path(self) -> str:
        try:
            from pathlib import Path as _P
            return str(_P(self.app.user_data_dir).resolve() / "favorites.json")
        except Exception:
            return str(Path("favorites.json").resolve())

    def _sync_favorite_icon(self) -> None:
        try:
            from utils.favorites_store import load_favorites
            fav = load_favorites(self._favorites_path())
            if self._molecule_key and self._molecule_key in fav.molecules:
                self.fav_icon = "star"
            else:
                self.fav_icon = "star-outline"
        except Exception:
            self.fav_icon = "star-outline"


    def action_reset_view(self) -> None:
        if self._viewer:
            try:
                self._viewer.reset_view()
            except Exception:
                pass

    def action_toggle_style(self) -> None:
        if not self._viewer:
            return
        try:
            style = self._viewer.toggle_style()
            txt = "шарики" if style == "balls" else "палочки"
            try:
                self.app.toast(f"Стиль: {txt}")
            except Exception:
                pass
        except Exception:
            return

    def action_toggle_bonds(self) -> None:
        if not self._viewer:
            return
        try:
            on = self._viewer.toggle_bond_emphasis()
            msg = "Связи: подсветка" if on else "Связи: обычные"
            try:
                self.app.toast(msg)
            except Exception:
                pass
        except Exception:
            return

    def action_screenshot(self) -> None:
        if not self._viewer:
            return
        try:
            from time import time
            base = Path(getattr(self.app, "user_data_dir", ".")).resolve() / "screenshots"
            base.mkdir(parents=True, exist_ok=True)
            k = self._molecule_key or "molecule"
            fname = f"{k}_{int(time())}.png"
            out = str(base / fname)
            ok = self._viewer.export_png(out)
            if ok:
                self.app.toast(f"Скриншот: {fname}")
            else:
                self.app.toast("Не удалось сохранить скриншот")
        except Exception:
            try:
                self.app.toast("Не удалось сохранить скриншот")
            except Exception:
                pass

    def action_toggle_favorite(self) -> None:
        if not self._molecule_key:
            return
        try:
            from utils.favorites_store import toggle_molecule
            state = toggle_molecule(self._favorites_path(), self._molecule_key)
            self.fav_icon = "star" if state else "star-outline"
            self.app.toast("Добавлено в избранное" if state else "Убрано из избранного")
        except Exception:
            try:
                self.app.toast("Не удалось обновить избранное")
            except Exception:
                pass

    def open_editor(self) -> None:
        """Открывает редактор молекулы с текущими данными."""
        nav = getattr(self.app, "nav_state", {}) or {}
        pdb_path = nav.get("pdb_path")
        title = nav.get("title", "Молекула")

        if pdb_path:
            self.app.open_molecule_editor(pdb_path, title)
