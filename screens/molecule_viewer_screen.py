
from __future__ import annotations

from pathlib import Path
from typing import Optional

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import Screen

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

from utils.molecule_parser import MoleculeParseError, parse_pdb
from utils.visualizer_3d import Visualizer3D


class MoleculeViewerScreen(Screen):
    """
    3D viewer screen.
    Data comes from app.nav_state:
      - pdb_path: str
      - title: str (e.g. "Вода (H2O)")
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._viewer: Optional[Visualizer3D] = None
        self._loaded_key: Optional[str] = None

    @property
    def app(self):
        from kivy.app import App
        return App.get_running_app()

    def on_pre_enter(self, *args):
        # рисуем после того, как KV ids готовы
        Clock.schedule_once(lambda *_: self._ensure_ui_and_load(), 0)

    def _ensure_ui_and_load(self) -> None:
        host = self.ids.get("viewer_host")
        if not host:
            Logger.warning("[MoleculeViewer] KV ids not ready: viewer_host missing")
            return

        nav = getattr(self.app, "nav_state", {}) or {}
        pdb_path = nav.get("pdb_path")
        title = nav.get("title", "Молекула")
        description = nav.get("description", "")

        # заголовок в TopBar
        try:
            self.app.set_top_title(title)
        except Exception:
            pass

        # заполняем описание
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
            host.clear_widgets()
            host.add_widget(MDLabel(
                text="Нет выбранной молекулы",
                halign="center",
                theme_text_color="Custom",
                text_color=getattr(self.app, "mm_text", (1, 1, 1, 1)),
            ))
            return

        # чтобы не грузить тот же файл по кругу
        key = str(pdb_path)
        if self._loaded_key == key and self._viewer is not None:
            return
        self._loaded_key = key

        host.clear_widgets()

        # карточка-подложка под 3D
        card = MDCard(
            md_bg_color=getattr(self.app, "mm_surface2", getattr(self.app, "mm_surface", (0.10, 0.11, 0.14, 1))),
            radius=[18, 18, 18, 18],
            padding=(dp(10), dp(10), dp(10), dp(10)),
            size_hint=(1, 1),
        )

        viewer = Visualizer3D()
        self._viewer = viewer
        card.add_widget(viewer)
        host.add_widget(card)

        # загрузка PDB
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

    def open_editor(self) -> None:
        """Открывает редактор молекулы с текущими данными."""
        nav = getattr(self.app, "nav_state", {}) or {}
        pdb_path = nav.get("pdb_path")
        title = nav.get("title", "Молекула")
        
        if pdb_path:
            self.app.open_molecule_editor(pdb_path, title)
