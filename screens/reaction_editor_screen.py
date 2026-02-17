from __future__ import annotations

import random
import re
from typing import Optional

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.logger import Logger
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen

from kivymd.uix.label import MDLabel

from utils.chem_types import Atom, bond_key, molecular_mass
from utils.molecule_parser import molecule_formula
from utils.visualizer_3d import Visualizer3D



SUBSTANCES = {

    "HCl": {
        "name": "Соляная кислота",
        "category": "acid",
        "atoms": [("H", 0, 0, 0), ("Cl", 1.3, 0, 0)],
        "bonds": [(0, 1)],
    },
    "H2SO4": {
        "name": "Серная кислота",
        "category": "acid",
        "atoms": [("S", 0, 0, 0), ("O", 1.4, 0, 0), ("O", -1.4, 0, 0), ("O", 0, 1.4, 0), ("O", 0, -1.4, 0), ("H", 0, 2.4, 0), ("H", 0, -2.4, 0)],
        "bonds": [(0, 1), (0, 2), (0, 3), (0, 4), (3, 5), (4, 6)],
    },
    "HNO3": {
        "name": "Азотная кислота",
        "category": "acid",
        "atoms": [("N", 0, 0, 0), ("O", 1.2, 0, 0), ("O", -0.6, 1.0, 0), ("O", -0.6, -1.0, 0), ("H", -1.5, 1.0, 0)],
        "bonds": [(0, 1), (0, 2), (0, 3), (2, 4)],
    },

    "NaOH": {
        "name": "Гидроксид натрия",
        "category": "base",
        "atoms": [("Na", 0, 0, 0), ("O", 2.0, 0, 0), ("H", 3.0, 0, 0)],
        "bonds": [(0, 1), (1, 2)],
    },
    "KOH": {
        "name": "Гидроксид калия",
        "category": "base",
        "atoms": [("K", 0, 0, 0), ("O", 2.2, 0, 0), ("H", 3.2, 0, 0)],
        "bonds": [(0, 1), (1, 2)],
    },
    "Ca(OH)2": {
        "name": "Гидроксид кальция",
        "category": "base",
        "atoms": [("Ca", 0, 0, 0), ("O", 2.0, 0.5, 0), ("H", 3.0, 0.5, 0), ("O", 2.0, -0.5, 0), ("H", 3.0, -0.5, 0)],
        "bonds": [(0, 1), (1, 2), (0, 3), (3, 4)],
    },

    "H2O": {
        "name": "Вода",
        "category": "other",
        "atoms": [("O", 0, 0, 0), ("H", 0.96, 0, 0), ("H", -0.24, 0.93, 0)],
        "bonds": [(0, 1), (0, 2)],
    },
    "CO2": {
        "name": "Углекислый газ",
        "category": "other",
        "atoms": [("C", 0, 0, 0), ("O", 1.2, 0, 0), ("O", -1.2, 0, 0)],
        "bonds": [(0, 1), (0, 2)],
    },
    "NH3": {
        "name": "Аммиак",
        "category": "other",
        "atoms": [("N", 0, 0, 0), ("H", 1.0, 0, 0), ("H", -0.5, 0.87, 0), ("H", -0.5, -0.87, 0)],
        "bonds": [(0, 1), (0, 2), (0, 3)],
    },

    "Na": {
        "name": "Натрий",
        "category": "metal",
        "atoms": [("Na", 0, 0, 0)],
        "bonds": [],
    },
    "K": {
        "name": "Калий",
        "category": "metal",
        "atoms": [("K", 0, 0, 0)],
        "bonds": [],
    },
    "Zn": {
        "name": "Цинк",
        "category": "metal",
        "atoms": [("Zn", 0, 0, 0)],
        "bonds": [],
    },
    "Fe": {
        "name": "Железо",
        "category": "metal",
        "atoms": [("Fe", 0, 0, 0)],
        "bonds": [],
    },

    "CH3OH": {
        "name": "Метанол",
        "category": "organic",
        "atoms": [("C", 0, 0, 0), ("O", 1.4, 0, 0), ("H", 1.9, 0.8, 0), ("H", -0.6, 0.9, 0), ("H", -0.6, -0.9, 0), ("H", 0, 0, 1.0)],
        "bonds": [(0, 1), (1, 2), (0, 3), (0, 4), (0, 5)],
    },
    "C2H5OH": {
        "name": "Этанол",
        "category": "organic",
        "atoms": [("C", 0, 0, 0), ("C", 1.5, 0, 0), ("O", 2.9, 0, 0), ("H", 3.4, 0.8, 0), ("H", -0.6, 0.9, 0), ("H", -0.6, -0.9, 0), ("H", 0, 0, 1.0), ("H", 1.5, 0.9, 0.5), ("H", 1.5, -0.9, 0.5)],
        "bonds": [(0, 1), (1, 2), (2, 3), (0, 4), (0, 5), (0, 6), (1, 7), (1, 8)],
    },
    "CH3COOH": {
        "name": "Уксусная кислота",
        "category": "organic",
        "atoms": [("C", 0, 0, 0), ("C", 1.5, 0, 0), ("O", 2.3, 1.0, 0), ("O", 2.3, -1.0, 0), ("H", 3.2, -1.0, 0), ("H", -0.6, 0.9, 0), ("H", -0.6, -0.9, 0), ("H", 0, 0, 1.0)],
        "bonds": [(0, 1), (1, 2), (1, 3), (3, 4), (0, 5), (0, 6), (0, 7)],
    },
}




KNOWN_REACTIONS_EDITOR = {

    frozenset(["HCl", "NaOH"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "HCl + NaOH -> NaCl + H2O",
        "products": "хлорид натрия (поваренная соль) и вода",
        "description": "Реакция нейтрализации. Выделяется тепло. Это экзотермическая реакция.",
        "effect": "heat",
    },
    frozenset(["HCl", "KOH"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "HCl + KOH -> KCl + H2O",
        "products": "хлорид калия и вода",
        "description": "Реакция нейтрализации. Выделяется тепло.",
        "effect": "heat",
    },
    frozenset(["H2SO4", "NaOH"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "H2SO4 + 2NaOH -> Na2SO4 + 2H2O",
        "products": "сульфат натрия и вода",
        "description": "Реакция нейтрализации серной кислоты. Сильно экзотермическая!",
        "effect": "heat",
    },

    frozenset(["Zn", "HCl"]): {
        "possible": True,
        "min_temp": 0,
        "equation": "Zn + 2HCl -> ZnCl2 + H2",
        "products": "хлорид цинка и водород",
        "description": "Цинк растворяется в кислоте. Выделяется газ водород (пузырьки)!",
        "effect": "gas",
    },
    frozenset(["Fe", "HCl"]): {
        "possible": True,
        "min_temp": 0,
        "equation": "Fe + 2HCl -> FeCl2 + H2",
        "products": "хлорид железа(II) и водород",
        "description": "Железо медленно растворяется. Выделяется водород.",
        "effect": "gas",
    },
    frozenset(["Na", "H2O"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "2Na + 2H2O -> 2NaOH + H2",
        "products": "гидроксид натрия и водород",
        "description": "ОПАСНО! Бурная реакция с выделением водорода и тепла. Может воспламениться!",
        "effect": "explosion",
    },
    frozenset(["K", "H2O"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "2K + 2H2O -> 2KOH + H2",
        "products": "гидроксид калия и водород",
        "description": "ОЧЕНЬ ОПАСНО! Калий реагирует ещё активнее натрия. Взрыв и пламя!",
        "effect": "explosion",
    },

    frozenset(["CO2", "NaOH"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "CO2 + 2NaOH -> Na2CO3 + H2O",
        "products": "карбонат натрия (сода) и вода",
        "description": "CO2 поглощается щёлочью. Так работают промышленные скрубберы.",
        "effect": "none",
    },
    frozenset(["CO2", "H2O"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "CO2 + H2O <-> H2CO3",
        "products": "угольная кислота (слабая, нестойкая)",
        "description": "Обратимая реакция. Угольная кислота быстро распадается обратно.",
        "effect": "none",
    },

    frozenset(["NH3", "HCl"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "NH3 + HCl -> NH4Cl",
        "products": "хлорид аммония",
        "description": "Образуется белый дым из мельчайших кристаллов хлорида аммония!",
        "effect": "smoke",
    },
    frozenset(["NH3", "H2O"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "NH3 + H2O <-> NH4OH",
        "products": "гидроксид аммония (нашатырный спирт)",
        "description": "Аммиак хорошо растворяется в воде. Резкий запах!",
        "effect": "none",
    },

    frozenset(["CH3COOH", "C2H5OH"]): {
        "possible": True,
        "min_temp": 60,
        "equation": "CH3COOH + C2H5OH -> CH3COOC2H5 + H2O",
        "products": "этилацетат (растворитель) и вода",
        "description": "Реакция этерификации. Требует нагрева и катализатора (H2SO4). Приятный фруктовый запах!",
        "effect": "none",
    },


    frozenset(["HCl", "Zn", "NH3"]): {
        "possible": True,
        "min_temp": 0,
        "equation": "Zn + 2HCl -> ZnCl2 + H2; NH3 + HCl -> NH4Cl",
        "products": "хлорид цинка, хлорид аммония и водород",
        "description": (
            "Здесь идут ДВЕ конкурирующие реакции:\n"
            "1) Цинк растворяется в кислоте: Zn + 2HCl -> ZnCl2 + H2 (выделяется газ)\n"
            "2) Аммиак связывается с кислотой: NH3 + HCl -> NH4Cl (белый дым)\n\n"
            "Обе реакции конкурируют за HCl! Что произойдёт раньше — зависит от количеств."
        ),
        "effect": "gas",
    },
    frozenset(["H2SO4", "Zn", "NH3"]): {
        "possible": True,
        "min_temp": 0,
        "equation": "Zn + H2SO4 -> ZnSO4 + H2; 2NH3 + H2SO4 -> (NH4)2SO4",
        "products": "сульфат цинка, сульфат аммония и водород",
        "description": (
            "Конкурирующие реакции:\n"
            "1) Цинк + серная кислота -> сульфат цинка + водород\n"
            "2) Аммиак + серная кислота -> сульфат аммония\n\n"
            "Обе реакции идут одновременно!"
        ),
        "effect": "gas",
    },
    frozenset(["HCl", "Fe", "NH3"]): {
        "possible": True,
        "min_temp": 0,
        "equation": "Fe + 2HCl -> FeCl2 + H2; NH3 + HCl -> NH4Cl",
        "products": "хлорид железа(II), хлорид аммония и водород",
        "description": (
            "Железо медленно растворяется в кислоте с выделением водорода.\n"
            "Аммиак быстро реагирует с HCl, образуя белый дым NH4Cl.\n"
            "Реакция аммиака быстрее, поэтому сначала образуется дым!"
        ),
        "effect": "smoke",
    },
    frozenset(["NaOH", "HCl", "Zn"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "NaOH + HCl -> NaCl + H2O; затем Zn + 2NaOH -> Na2ZnO2 + H2",
        "products": "хлорид натрия, цинкат натрия и водород",
        "description": (
            "Сначала идёт нейтрализация: NaOH + HCl -> NaCl + H2O\n"
            "Если NaOH в избытке, цинк растворяется в щёлочи!\n"
            "Zn + 2NaOH -> Na2ZnO2 + H2 (цинк — амфотерный металл)"
        ),
        "effect": "gas",
    },
    frozenset(["Na", "H2O", "HCl"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "2Na + 2H2O -> 2NaOH + H2; NaOH + HCl -> NaCl + H2O",
        "products": "хлорид натрия, вода и водород",
        "description": (
            "ОПАСНО! Натрий бурно реагирует с водой!\n"
            "2Na + 2H2O -> 2NaOH + H2 (взрыв, пламя!)\n"
            "Образовавшийся NaOH нейтрализуется кислотой.\n"
            "В итоге получается соль NaCl."
        ),
        "effect": "explosion",
    },
    frozenset(["K", "H2O", "HCl"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "2K + 2H2O -> 2KOH + H2; KOH + HCl -> KCl + H2O",
        "products": "хлорид калия, вода и водород",
        "description": (
            "ОЧЕНЬ ОПАСНО! Калий ещё активнее натрия!\n"
            "Взрыв и фиолетовое пламя!\n"
            "Результат: KCl (хлорид калия)."
        ),
        "effect": "explosion",
    },
    frozenset(["NH3", "HCl", "H2O"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "NH3 + HCl -> NH4Cl",
        "products": "хлорид аммония (растворённый в воде)",
        "description": (
            "Аммиак реагирует с соляной кислотой:\n"
            "NH3 + HCl -> NH4Cl\n\n"
            "В присутствии воды хлорид аммония растворяется.\n"
            "Получается раствор нашатыря (NH4Cl)."
        ),
        "effect": "none",
    },
    frozenset(["CO2", "NaOH", "H2O"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "CO2 + 2NaOH -> Na2CO3 + H2O",
        "products": "карбонат натрия (сода) в растворе",
        "description": (
            "CO2 поглощается раствором щёлочи.\n"
            "Образуется карбонат натрия (стиральная сода).\n"
            "Так работают промышленные очистители воздуха!"
        ),
        "effect": "none",
    },
    frozenset(["CH3COOH", "NaOH", "H2O"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "CH3COOH + NaOH -> CH3COONa + H2O",
        "products": "ацетат натрия в водном растворе",
        "description": (
            "Нейтрализация уксусной кислоты щёлочью.\n"
            "Получается ацетат натрия — используется как консервант (E262).\n"
            "Раствор имеет слабощелочную реакцию."
        ),
        "effect": "heat",
    },

    frozenset(["H2O", "NaOH"]): {
        "possible": False,
        "description": "NaOH уже растворён в воде. Химической реакции не происходит, только растворение.",
    },
    frozenset(["CH3OH", "H2O"]): {
        "possible": False,
        "description": "Метанол и вода просто смешиваются. Химической реакции нет.",
    },
    frozenset(["C2H5OH", "H2O"]): {
        "possible": False,
        "description": "Этанол и вода смешиваются в любых пропорциях. Это просто разбавление.",
    },
}


class ReactionEditorScreen(Screen):
    """Эксперименты с реакциями."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._viewer: Optional[Visualizer3D] = None
        self._current_atoms: list[Atom] = []
        self._current_bonds: list[tuple[int, int]] = []
        self._highlight_break: list[tuple[int, int]] = []
        self._highlight_form: list[tuple[int, int]] = []


        self._molecule_groups: list[list[int]] = []

        self._temperature: float = 25.0
        self._added_substances: list[str] = []
        self._reaction_done: bool = False

    @property
    def app(self):
        from kivy.app import App
        return App.get_running_app()

    def on_pre_enter(self, *args):
        Clock.schedule_once(lambda *_: self._ensure_ui(), 0)

    def _ensure_ui(self) -> None:
        host = self.ids.get("editor_host")
        if not host:
            Logger.warning("[ReactionEditor] KV ids not ready: editor_host missing")
            return

        try:
            self.app.set_top_title("Похимичим!")
        except Exception:
            pass

        host.clear_widgets()


        card = BoxLayout(
            orientation="vertical",
            padding=[dp(10), dp(10), dp(10), dp(10)],
            size_hint=(1, 1),
        )
        bg_color = getattr(self.app, "mm_surface2", (0.10, 0.11, 0.14, 1))
        with card.canvas.before:
            Color(*bg_color)
            card._bg_rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[18, 18, 18, 18])
        card.bind(
            pos=lambda *_: setattr(card._bg_rect, 'pos', card.pos),
            size=lambda *_: setattr(card._bg_rect, 'size', card.size),
        )

        self._viewer = Visualizer3D()
        card.add_widget(self._viewer)
        host.add_widget(card)


        self._reset_all()

    def _reset_all(self) -> None:
        """Полный сброс редактора."""
        self._current_atoms = []
        self._current_bonds = []
        self._highlight_break = []
        self._highlight_form = []
        self._molecule_groups = []
        self._temperature = 25.0
        self._added_substances = []
        self._reaction_done = False


        temp_slider = self.ids.get("temp_slider")
        if temp_slider:
            temp_slider.value = 25.0

        self._update_viewer()
        self._update_info()
        self._update_temp_label()
        self._update_slider_color()

    def _update_viewer(self) -> None:
        if self._viewer:
            self._viewer.set_scene(
                self._current_atoms,
                self._current_bonds,
                highlight_break=self._highlight_break,
                highlight_form=self._highlight_form,
                groups=self._molecule_groups,
            )

    def _update_info(self) -> None:
        info_label = self.ids.get("info_label")
        if not info_label:
            return

        if not self._current_atoms:
            info_label.text = "Пусто. Добавьте вещества."
            return

        formula = molecule_formula(self._current_atoms)
        mass = molecular_mass(self._current_atoms)
        substances = " + ".join(self._added_substances) if self._added_substances else "?"

        info_label.text = f"{substances}  |  {formula}  |  {mass:.2f} г/моль"

    def _update_temp_label(self) -> None:
        temp_label = self.ids.get("temp_label")
        if temp_label:
            temp_label.text = f"{self._temperature:.0f} C"

    def _update_slider_color(self) -> None:
        temp_slider = self.ids.get("temp_slider")
        temp_label = self.ids.get("temp_label")
        if not temp_slider:
            return

        t = (self._temperature + 200) / 700

        if t < 0.32:
            ratio = t / 0.32
            r = 0.2 + ratio * 0.8
            g = 0.5 + ratio * 0.5
            b = 0.95
        else:
            ratio = (t - 0.32) / 0.68
            r = 0.95
            g = 1.0 - ratio * 0.7
            b = 1.0 - ratio * 0.8

        color = (r, g, b, 1)

        try:
            temp_slider.track_active_color = color
            temp_slider.thumb_color = color
        except Exception:
            pass

        if temp_label:
            temp_label.text_color = color

    def _show_message(self, text: str, permanent: bool = False) -> None:
        """Показывает сообщение в заголовке над 3D областью."""
        msg_label = self.ids.get("message_label")
        if msg_label:
            msg_label.text = text
            Clock.unschedule(self._clear_message)
            if not permanent:
                Clock.schedule_once(self._clear_message, 4.0)

    def _clear_message(self, *_):
        """Возвращает заголовок к исходному тексту."""
        msg_label = self.ids.get("message_label")
        if msg_label:
            msg_label.text = "Выберите вещества для смешивания"

    def on_temperature_change(self, value: float) -> None:
        self._temperature = value
        self._update_temp_label()
        self._update_slider_color()

    def show_substance_menu(self, category: str) -> None:
        """Показывает меню выбора веществ над кнопкой."""
        from kivymd.uix.menu import MDDropdownMenu

        menu_items = []
        for key, data in SUBSTANCES.items():
            if data["category"] == category:
                menu_items.append({
                    "text": f"{data['name']} ({key})",
                    "font_size": sp(12),
                    "height": dp(36),
                    "on_release": lambda k=key: self._add_substance(k),
                })

        if not menu_items:
            self._show_message(f"Нет веществ в категории")
            return


        caller = None
        if category == "acid":
            caller = self.ids.get("btn_acid")
        elif category == "base":
            caller = self.ids.get("btn_base")
        elif category == "metal":
            caller = self.ids.get("btn_metal")
        elif category == "other":
            caller = self.ids.get("btn_other")
        elif category == "organic":
            caller = self.ids.get("btn_organic")

        if not caller:
            return


        menu_width = dp(160)


        max_height = min(dp(300), Window.height * 0.5)

        self._substance_menu = MDDropdownMenu(
            caller=caller,
            items=menu_items,
            width=menu_width,
            position="auto",
            max_height=max_height,
        )
        self._substance_menu.open()

    def _add_substance(self, substance_key: str) -> None:
        """Добавляет вещество в смесь."""
        if hasattr(self, '_substance_menu') and self._substance_menu:
            self._substance_menu.dismiss()

        if substance_key not in SUBSTANCES:
            self._show_message("Неизвестное вещество")
            return

        if self._reaction_done:
            self._show_message("Сначала сбросьте результат")
            return

        if len(self._added_substances) >= 3:
            self._show_message("Максимум 3 вещества")
            return

        if substance_key in self._added_substances:
            self._show_message(f"{substance_key} уже добавлен")
            return

        substance = SUBSTANCES[substance_key]


        if self._current_atoms:
            max_x = max(a.x for a in self._current_atoms)
            offset_x = max_x + 2.5
        else:
            offset_x = 0.0


        base_idx = len(self._current_atoms)
        new_group_indices = []

        for (element, x, y, z) in substance["atoms"]:
            new_atom = Atom(element=element, x=x + offset_x, y=y, z=z)
            self._current_atoms.append(new_atom)
            new_group_indices.append(len(self._current_atoms) - 1)


        for (i, j) in substance["bonds"]:
            self._current_bonds.append((base_idx + i, base_idx + j))
            self._highlight_form.append(bond_key(base_idx + i, base_idx + j))


        self._molecule_groups.append(new_group_indices)

        self._added_substances.append(substance_key)

        self._update_viewer()
        self._update_info()
        self._show_message(f"+ {substance['name']}")


        def clear_highlight(*_):
            self._highlight_form = []
            self._update_viewer()
        Clock.schedule_once(clear_highlight, 1.2)

    def run_reaction(self) -> None:
        """Запускает реакцию между добавленными веществами."""
        if len(self._added_substances) < 2:
            self._show_message("Добавьте минимум 2 вещества")
            return

        if self._reaction_done:
            self._show_message("Реакция уже прошла. Сбросьте для новой.")
            return

        self._show_message("Анализирую реакцию...")


        self._analyze_reaction_with_ai()

    def _analyze_reaction_with_ai(self) -> None:
        """Анализируем реакцию с помощью ИИ и показываем результат с анимацией."""
        substances_str = " + ".join(self._added_substances)


        prompt = (
            f"{substances_str} при {self._temperature:.0f} C.\n"
            f"Начни с: РЕАКЦИЯ: / СМЕШИВАНИЕ: / НЕВОЗМОЖНО:\n"
            f"Затем: уравнение, продукты, наблюдения. Кратко, 3-4 предложения."
        )

        if not self.app._ai_engine:
            self._show_message("ИИ недоступен. Подключите интернет или скачайте оффлайн-модель.")
            return

        def work():
            try:

                answer = self.app._ai_engine.ask(prompt, verify=False, max_tokens=200)
                answer_stripped = answer.strip()
                answer_lower = answer_stripped.lower()


                is_hallucination = False
                words = answer_stripped.split()
                if len(words) > 20:
                    phrase_counts = {}
                    for i in range(len(words) - 4):
                        phrase = " ".join(words[i:i+5])
                        phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
                    if any(count > 2 for count in phrase_counts.values()):
                        is_hallucination = True


                is_failed = is_hallucination or len(answer_stripped) < 20

                if is_failed:

                    Clock.schedule_once(
                        lambda *_: self._show_ai_error(), 0
                    )
                    return


                show_animation = False

                if answer_lower.startswith("реакция:") or answer_lower.startswith("реакция "):
                    title = "Химическая реакция"
                    show_animation = True
                    result_text = answer_stripped[8:].strip() if answer_lower.startswith("реакция:") else answer_stripped
                elif answer_lower.startswith("смешивание:") or answer_lower.startswith("смешивание "):
                    title = "Смешивание веществ"
                    show_animation = True
                    result_text = answer_stripped[11:].strip() if answer_lower.startswith("смешивание:") else answer_stripped
                elif answer_lower.startswith("невозможно:") or answer_lower.startswith("невозможно "):
                    title = "Реакция невозможна"
                    show_animation = False
                    result_text = answer_stripped[11:].strip() if answer_lower.startswith("невозможно:") else answer_stripped
                else:

                    if any(word in answer_lower for word in ["невозможн", "не реагируют", "не смешиваются", "опасно", "нельзя"]):
                        title = "Реакция невозможна"
                        show_animation = False
                    elif any(word in answer_lower for word in ["->", "=", "образуется", "получается", "реагирует", "гидролиз", "окисление"]):
                        title = "Химическая реакция"
                        show_animation = True
                    elif any(word in answer_lower for word in ["растворяется", "смешивается", "диссоциирует", "растворение"]):
                        title = "Смешивание веществ"
                        show_animation = True
                    else:
                        title = "Результат анализа"
                        show_animation = True
                    result_text = answer_stripped


                if show_animation:
                    Clock.schedule_once(lambda *_: self._run_reaction_animation(result_text, title), 0)
                else:

                    def show_no_anim(*_):
                        self._reaction_done = True
                        self._show_reaction_result(result_text, title=title)
                    Clock.schedule_once(show_no_anim, 0)

            except Exception as e:
                Logger.exception(f"[ReactionEditor] AI error: {e}")
                Clock.schedule_once(
                    lambda *_: self._show_message("Ошибка ИИ. Проверьте подключение."), 0
                )

        self.app._executor.submit(work)

    def _show_ai_error(self) -> None:
        """Показывает ошибку анализа ИИ."""
        self._reaction_done = True
        self._show_reaction_result(
            "Не удалось проанализировать эту комбинацию.\n\n"
            "Попробуйте другие вещества.",
            title="Ошибка анализа"
        )

    def _run_reaction_animation(self, result_text: str, title: str) -> None:
        """Запускает анимацию реакции и показывает результат."""
        self._reaction_done = True

        if not self._current_bonds:

            self._show_reaction_result(result_text, title=title)
            return

        self._show_message("Реакция идёт...")


        num_to_break = max(1, min(3, len(self._current_bonds) // 3))
        bonds_to_break = random.sample(self._current_bonds, num_to_break)
        self._highlight_break = [bond_key(b[0], b[1]) for b in bonds_to_break]
        self._update_viewer()


        def phase2(*_):
            for b in bonds_to_break:
                if b in self._current_bonds:
                    self._current_bonds.remove(b)
                elif (b[1], b[0]) in self._current_bonds:
                    self._current_bonds.remove((b[1], b[0]))
            self._highlight_break = []
            self._update_viewer()

        Clock.schedule_once(phase2, 0.8)


        def phase3(*_):
            new_bonds = []
            for i, atom_i in enumerate(self._current_atoms):
                for j, atom_j in enumerate(self._current_atoms):
                    if i >= j:
                        continue
                    bond = (min(i, j), max(i, j))
                    if bond in self._current_bonds:
                        continue
                    dist = ((atom_i.x - atom_j.x)**2 + (atom_i.y - atom_j.y)**2 + (atom_i.z - atom_j.z)**2) ** 0.5
                    if dist < 2.8 and len(new_bonds) < 3:
                        self._current_bonds.append(bond)
                        new_bonds.append(bond)

            self._highlight_form = [bond_key(b[0], b[1]) for b in new_bonds]
            self._update_viewer()

        Clock.schedule_once(phase3, 1.5)


        def phase4(*_):
            self._highlight_form = []
            self._highlight_break = []
            self._update_viewer()
            self._update_info()
            self._show_reaction_result(result_text, title=title)

        Clock.schedule_once(phase4, 2.5)

    def _show_reaction_result(self, text: str, title: str = "Результат") -> None:
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.dialog.dialog import (
            MDDialogHeadlineText,
            MDDialogSupportingText,
            MDDialogButtonContainer,
        )
        from kivymd.uix.button import MDButton, MDButtonText

        dialog = MDDialog(
            MDDialogHeadlineText(text=title),
            MDDialogSupportingText(text=text),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="OK"),
                    style="text",
                    on_release=lambda *_: dialog.dismiss(),
                ),
            ),
        )
        dialog.open()

    def reset_editor(self) -> None:
        """Сброс редактора к начальному состоянию."""
        self._reset_all()
        self._clear_message()
