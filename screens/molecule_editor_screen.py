from __future__ import annotations

import random
from pathlib import Path
from typing import Optional

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.logger import Logger
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from kivymd.uix.label import MDLabel

from utils.chem_types import Atom, bond_key, molecular_mass
from utils.molecule_parser import MoleculeParseError, molecule_formula, parse_pdb
from utils.visualizer_3d import Visualizer3D



REAGENTS = {
    "HCl": {"name": "Соляная кислота (HCl)", "atoms": [("H", 0, 0, 0), ("Cl", 1.3, 0, 0)], "bonds": [(0, 1)]},
    "H2SO4": {"name": "Серная кислота (H2SO4)", "atoms": [("S", 0, 0, 0), ("O", 1.4, 0, 0), ("O", -1.4, 0, 0), ("O", 0, 1.4, 0), ("O", 0, -1.4, 0), ("H", 0, 2.4, 0), ("H", 0, -2.4, 0)], "bonds": [(0, 1), (0, 2), (0, 3), (0, 4), (3, 5), (4, 6)]},
    "HNO3": {"name": "Азотная кислота (HNO3)", "atoms": [("N", 0, 0, 0), ("O", 1.2, 0, 0), ("O", -0.6, 1.0, 0), ("O", -0.6, -1.0, 0), ("H", -1.5, 1.0, 0)], "bonds": [(0, 1), (0, 2), (0, 3), (2, 4)]},
    "NaOH": {"name": "Гидроксид натрия (NaOH)", "atoms": [("Na", 0, 0, 0), ("O", 2.0, 0, 0), ("H", 3.0, 0, 0)], "bonds": [(0, 1), (1, 2)]},
    "H2O": {"name": "Вода (H2O)", "atoms": [("O", 0, 0, 0), ("H", 0.96, 0, 0), ("H", -0.24, 0.93, 0)], "bonds": [(0, 1), (0, 2)]},
    "NH3": {"name": "Аммиак (NH3)", "atoms": [("N", 0, 0, 0), ("H", 1.0, 0, 0), ("H", -0.5, 0.87, 0), ("H", -0.5, -0.87, 0)], "bonds": [(0, 1), (0, 2), (0, 3)]},
    "CH3OH": {"name": "Метанол (CH3OH)", "atoms": [("C", 0, 0, 0), ("O", 1.4, 0, 0), ("H", 1.9, 0.8, 0), ("H", -0.6, 0.9, 0), ("H", -0.6, -0.9, 0), ("H", 0, 0, 1.0)], "bonds": [(0, 1), (1, 2), (0, 3), (0, 4), (0, 5)]},
    "CO2": {"name": "Углекислый газ (CO2)", "atoms": [("C", 0, 0, 0), ("O", 1.2, 0, 0), ("O", -1.2, 0, 0)], "bonds": [(0, 1), (0, 2)]},
    "C2H5OH": {"name": "Этанол (C2H5OH)", "atoms": [("C", 0, 0, 0), ("C", 1.5, 0, 0), ("O", 2.9, 0, 0), ("H", 3.4, 0.8, 0), ("H", -0.6, 0.9, 0), ("H", -0.6, -0.9, 0), ("H", 0, 0, 1.0), ("H", 1.5, 0.9, 0.6), ("H", 1.5, -0.9, 0.6)], "bonds": [(0, 1), (1, 2), (2, 3), (0, 4), (0, 5), (0, 6), (1, 7), (1, 8)]},
    "Aspirin": {"name": "Аспирин (C9H8O4)", "atoms": [("C", 0, 0, 0), ("C", 1.4, 0, 0), ("C", 2.1, 1.2, 0), ("C", 1.4, 2.4, 0), ("C", 0, 2.4, 0), ("C", -0.7, 1.2, 0), ("O", 2.8, 3.6, 0), ("C", 2.1, 4.8, 0), ("O", 2.8, 6.0, 0), ("C", -1.4, 1.2, 0), ("O", -2.1, 0, 0), ("O", -2.1, 2.4, 0)], "bonds": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (3, 6), (6, 7), (7, 8), (5, 9), (9, 10), (9, 11)]},
    "NaCl": {"name": "Хлорид натрия (NaCl)", "atoms": [("Na", 0, 0, 0), ("Cl", 2.4, 0, 0)], "bonds": [(0, 1)]},
}





KNOWN_REACTIONS = {

    frozenset(["HCl", "NaOH"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "HCl + NaOH -> NaCl + H2O",
        "products": "хлорид натрия (поваренная соль) и вода",
        "description": "Реакция нейтрализации. Соляная кислота реагирует с гидроксидом натрия, образуя соль и воду.",
    },
    frozenset(["H2SO4", "NaOH"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "H2SO4 + 2NaOH -> Na2SO4 + 2H2O",
        "products": "сульфат натрия и вода",
        "description": "Реакция нейтрализации серной кислоты гидроксидом натрия.",
    },
    frozenset(["HNO3", "NaOH"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "HNO3 + NaOH -> NaNO3 + H2O",
        "products": "нитрат натрия и вода",
        "description": "Реакция нейтрализации азотной кислоты гидроксидом натрия.",
    },

    frozenset(["CH3OH", "HCl"]): {
        "possible": True,
        "min_temp": 50,
        "equation": "CH3OH + HCl -> CH3Cl + H2O",
        "products": "хлорметан (метилхлорид) и вода",
        "description": "Реакция замещения гидроксильной группы на хлор. Требует нагревания.",
    },

    frozenset(["NH3", "HCl"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "NH3 + HCl -> NH4Cl",
        "products": "хлорид аммония",
        "description": "Аммиак реагирует с соляной кислотой, образуя белый дым хлорида аммония.",
    },
    frozenset(["NH3", "H2SO4"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "2NH3 + H2SO4 -> (NH4)2SO4",
        "products": "сульфат аммония",
        "description": "Аммиак реагирует с серной кислотой, образуя сульфат аммония — удобрение.",
    },

    frozenset(["H2O", "CO2"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "H2O + CO2 <-> H2CO3",
        "products": "угольная кислота (слабая, нестойкая)",
        "description": "Углекислый газ растворяется в воде, образуя слабую угольную кислоту. Реакция обратимая.",
    },
    frozenset(["H2O", "NH3"]): {
        "possible": True,
        "min_temp": -50,
        "equation": "H2O + NH3 <-> NH4OH",
        "products": "гидроксид аммония (нашатырный спирт)",
        "description": "Аммиак хорошо растворяется в воде, образуя слабое основание — нашатырный спирт.",
    },

    frozenset(["CH3OH", "H2O"]): {
        "possible": False,
        "min_temp": 0,
        "equation": "",
        "products": "",
        "description": "Метанол и вода не вступают в химическую реакцию. Они просто смешиваются в любых пропорциях (оба — полярные растворители).",
    },

    frozenset(["C2H5OH", "H2O"]): {
        "possible": False,
        "min_temp": 0,
        "equation": "",
        "products": "",
        "description": "Этанол и вода не вступают в химическую реакцию. Они смешиваются в любых пропорциях. Так получают водку и другие алкогольные напитки.",
    },

    frozenset(["Aspirin", "H2O"]): {
        "possible": True,
        "min_temp": 20,
        "equation": "C9H8O4 + H2O -> C7H6O3 + C2H4O2",
        "products": "салициловая кислота и уксусная кислота",
        "description": "Аспирин (ацетилсалициловая кислота) медленно гидролизуется в воде, распадаясь на салициловую и уксусную кислоты. Этот процесс ускоряется при нагревании. Именно поэтому аспирин хранят в сухом месте.",
    },

    frozenset(["Aspirin", "NaOH"]): {
        "possible": True,
        "min_temp": 0,
        "equation": "C9H8O4 + 2NaOH -> C7H5O3Na + C2H3O2Na + H2O",
        "products": "салицилат натрия и ацетат натрия",
        "description": "Аспирин быстро реагирует с щёлочью (гидролиз в щелочной среде). Образуются соли салициловой и уксусной кислот.",
    },

    frozenset(["C2H5OH", "HCl"]): {
        "possible": True,
        "min_temp": 60,
        "equation": "C2H5OH + HCl -> C2H5Cl + H2O",
        "products": "хлорэтан (этилхлорид) и вода",
        "description": "Этанол реагирует с соляной кислотой при нагревании, образуя хлорэтан. Реакция замещения гидроксильной группы.",
    },

    frozenset(["NaCl", "H2O"]): {
        "possible": False,
        "min_temp": 0,
        "equation": "",
        "products": "",
        "description": "Поваренная соль (NaCl) просто растворяется в воде, диссоциируя на ионы Na+ и Cl-. Химической реакции не происходит, это физический процесс растворения.",
    },
}


class MoleculeEditorScreen(Screen):


    """Эксперименты с молекулой."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._viewer: Optional[Visualizer3D] = None
        self._original_atoms: list[Atom] = []
        self._original_bonds: list[tuple[int, int]] = []
        self._current_atoms: list[Atom] = []
        self._current_bonds: list[tuple[int, int]] = []
        self._highlight_break: list[tuple[int, int]] = []
        self._highlight_form: list[tuple[int, int]] = []

        self._temperature: float = 25.0
        self._message_label: Optional[MDLabel] = None
        self._temp_label: Optional[MDLabel] = None
        self._selected_reagent: Optional[str] = None
        self._reagent_menu_anchor: Optional[Widget] = None


        self._bond_mode: bool = False
        self._first_atom_idx: Optional[int] = None


        self._added_reagents: list[str] = []


        self._reagent_added: bool = False

    @property
    def app(self):
        from kivy.app import App
        return App.get_running_app()

    def on_pre_enter(self, *args):
        Clock.schedule_once(lambda *_: self._ensure_ui_and_load(), 0)

    def _ensure_ui_and_load(self) -> None:
        host = self.ids.get("editor_host")
        if not host:
            Logger.warning("[MoleculeEditor] KV ids not ready: editor_host missing")
            return

        nav = getattr(self.app, "nav_state", {}) or {}
        pdb_path = nav.get("pdb_path")
        title = nav.get("title", "Редактор")

        try:
            self.app.set_top_title(f"Редактор: {title}")
        except Exception:
            pass

        if not pdb_path:
            host.clear_widgets()
            host.add_widget(MDLabel(
                text="Нет выбранной молекулы",
                halign="center",
                theme_text_color="Custom",
                text_color=getattr(self.app, "mm_text", (1, 1, 1, 1)),
            ))
            return

        try:
            mol = parse_pdb(str(Path(pdb_path)))
            self._original_atoms = list(mol.atoms)
            self._original_bonds = list(mol.bonds)
            self._current_atoms = list(mol.atoms)
            self._current_bonds = list(mol.bonds)
        except MoleculeParseError as e:
            Logger.exception(f"[MoleculeEditor] parse error: {e}")
            host.clear_widgets()
            host.add_widget(MDLabel(
                text=f"Не удалось открыть PDB:\n{e}",
                halign="center",
                theme_text_color="Custom",
                text_color=getattr(self.app, "mm_text", (1, 1, 1, 1)),
            ))
            return

        host.clear_widgets()

        self._viewer = Visualizer3D()

        self._viewer.edit_mode = True
        self._viewer.on_atom_tap = self._on_atom_tap
        self._viewer.on_bond_tap = self._on_bond_tap

        host.add_widget(self._viewer)


        self._temperature = 25.0
        self._highlight_break = []
        self._highlight_form = []
        self._reagent_added = False
        self._added_reagents = []
        self._bond_mode = False
        self._first_atom_idx = None

        self._update_viewer()
        self._update_info()
        self._update_temp_label()
        self._update_slider_color()
        self._update_run_button()
        self._show_message("Тапните атом или связь для удаления")

    def _on_atom_tap(self, atom_idx: int) -> None:
        """Обработка тапа по атому."""
        if atom_idx < 0 or atom_idx >= len(self._current_atoms):
            return


        if self._bond_mode:
            self._handle_bond_mode_tap(atom_idx)
            return


        atom = self._current_atoms[atom_idx]
        element = atom.element


        new_atoms = []
        old_to_new: dict[int, int] = {}

        for i, a in enumerate(self._current_atoms):
            if i != atom_idx:
                new_idx = len(new_atoms)
                new_atoms.append(a)
                old_to_new[i] = new_idx

        new_bonds = []
        for (i, j) in self._current_bonds:
            if i != atom_idx and j != atom_idx:
                new_i = old_to_new.get(i)
                new_j = old_to_new.get(j)
                if new_i is not None and new_j is not None:
                    new_bonds.append((new_i, new_j) if new_i < new_j else (new_j, new_i))

        self._current_atoms = new_atoms
        self._current_bonds = new_bonds
        self._update_viewer()
        self._update_info()
        self._show_message(f"Удалён атом: {element}")

    def _handle_bond_mode_tap(self, atom_idx: int) -> None:
        """Обработка тапа в режиме создания связей."""
        if self._first_atom_idx is None:

            self._first_atom_idx = atom_idx
            atom = self._current_atoms[atom_idx]
            self._show_message(f"Выбран {atom.element}. Тапните второй атом")
        else:

            if self._first_atom_idx == atom_idx:
                self._show_message("Нельзя связать атом с самим собой")
                self._first_atom_idx = None
                return


            bond = (min(self._first_atom_idx, atom_idx), max(self._first_atom_idx, atom_idx))
            if bond in self._current_bonds:
                self._show_message("Связь уже существует")
                self._first_atom_idx = None
                return


            self._current_bonds.append(bond)
            self._highlight_form.append(bond_key(bond[0], bond[1]))

            a1 = self._current_atoms[self._first_atom_idx]
            a2 = self._current_atoms[atom_idx]
            self._show_message(f"Связь {a1.element}-{a2.element} создана")

            self._first_atom_idx = None
            self._update_viewer()
            self._update_info()


            def clear_highlight(*_):
                self._highlight_form = []
                self._update_viewer()
            Clock.schedule_once(clear_highlight, 1.5)

    def _on_bond_tap(self, bond: tuple[int, int]) -> None:
        """Обработка тапа по связи — удаление (в режиме удаления)."""
        if self._bond_mode:

            return


        if bond in self._current_bonds:
            self._current_bonds.remove(bond)
        elif (bond[1], bond[0]) in self._current_bonds:
            self._current_bonds.remove((bond[1], bond[0]))
        else:
            self._show_message("Связь не найдена")
            return

        self._update_viewer()
        self._update_info()
        self._show_message("Связь удалена")

    def _update_viewer(self) -> None:
        if self._viewer:
            self._viewer.set_scene(
                self._current_atoms,
                self._current_bonds,
                highlight_break=self._highlight_break,
                highlight_form=self._highlight_form,
            )

    def _update_info(self) -> None:
        info_label = self.ids.get("info_label")
        if not info_label:
            return

        formula = molecule_formula(self._current_atoms)
        mass = molecular_mass(self._current_atoms)

        info_label.text = f"Полученная структура: {formula}  |  {mass:.2f} г/моль"

    def _update_temp_label(self) -> None:
        temp_label = self.ids.get("temp_label")
        if temp_label:
            temp_label.text = f"{self._temperature:.0f} C"

    def _show_message(self, text: str) -> None:
        """Показывает сообщение в UI."""
        msg_label = self.ids.get("message_label")
        if msg_label:
            msg_label.text = text

            Clock.unschedule(self._clear_message)
            Clock.schedule_once(self._clear_message, 3.0)

    def _clear_message(self, *_):
        msg_label = self.ids.get("message_label")
        if msg_label:
            msg_label.text = ""

    def on_temperature_change(self, value: float) -> None:
        """Обработка изменения температуры."""
        self._temperature = value
        self._update_temp_label()
        self._update_slider_color()
        self._apply_temperature_effect()

    def _update_slider_color(self) -> None:
        """Обновляет цвет слайдера в зависимости от температуры."""
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

    def _apply_temperature_effect(self) -> None:
        """Применяет эффект температуры к молекуле."""
        if not self._current_bonds:
            return


        if self._temperature > 100:
            break_chance = (self._temperature - 100) / 500
            if random.random() < break_chance and self._current_bonds:

                bond_idx = random.randint(0, len(self._current_bonds) - 1)
                broken = self._current_bonds.pop(bond_idx)
                self._highlight_break.append(bond_key(broken[0], broken[1]))
                self._update_viewer()
                self._update_info()
                self._show_message(f"Связь разорвана при {self._temperature:.0f} C!")


        elif self._temperature < -50:
            self._show_message(f"Молекула заморожена при {self._temperature:.0f} C")

    def toggle_bond_mode(self) -> None:
        """Переключение режима: удаление <-> связывание."""
        self._bond_mode = not self._bond_mode
        self._first_atom_idx = None

        if self._bond_mode:
            self._show_message("Режим связывания: тапните два атома")
        else:
            self._show_message("Режим удаления: тапните атом или связь")

        self._update_mode_button()

    def _update_mode_button(self) -> None:
        """Обновляет текст кнопки режима."""
        mode_label = self.ids.get("mode_label")
        if mode_label:

            if self._bond_mode:
                mode_label.text = "Удалять"
            else:
                mode_label.text = "Связать"

    def reset_molecule(self) -> None:
        """Сброс молекулы к исходному состоянию."""
        self._current_atoms = list(self._original_atoms)
        self._current_bonds = list(self._original_bonds)
        self._highlight_break = []
        self._highlight_form = []
        self._temperature = 25.0
        self._bond_mode = False
        self._first_atom_idx = None
        self._reagent_added = False
        self._added_reagents = []


        temp_slider = self.ids.get("temp_slider")
        if temp_slider:
            temp_slider.value = 25.0

        self._update_viewer()
        self._update_info()
        self._update_temp_label()
        self._update_slider_color()
        self._update_mode_button()
        self._update_run_button()
        self._show_message("Молекула восстановлена")

    def identify_molecule(self) -> None:
        """Спросить ИИ: что это за молекула."""
        if not self._current_atoms:
            self._show_message("Нет атомов для анализа")
            return

        formula = molecule_formula(self._current_atoms)


        atom_counts: dict[str, int] = {}
        for atom in self._current_atoms:
            atom_counts[atom.element] = atom_counts.get(atom.element, 0) + 1
        atom_list = ", ".join(f"{el}: {cnt}" for el, cnt in sorted(atom_counts.items()))


        prompt = (
            "Это результат учебной 3D-симуляции. Структура может быть нереальной или смесью фрагментов.\n"
            f"Формула: {formula}.\n"
            f"Состав по атомам: {atom_list}.\n\n"
            "Задание: если это известное школьное вещество — назови его и класс. "
            "Если по формуле/составу нельзя уверенно определить — напиши только 'Я не знаю точного ответа' "
            "и кратко объясни, почему (например, мало данных, нужна структура/условия, похоже на смесь/разложение). "
            "Не подставляй другие вещества и не пиши чужие формулы."
        )

        if not self.app._ai_engine:
            self._show_message("ИИ недоступен")
            return

        self._show_message("Анализирую...")

        def work():
            try:

                answer = self.app._ai_engine.ask(prompt, verify=True, max_tokens=220)
                Clock.schedule_once(lambda *_: self._show_ai_result(answer), 0)
            except Exception as e:
                Logger.exception(f"[MoleculeEditor] AI error: {e}")
                Clock.schedule_once(lambda *_: self._show_message(f"Ошибка ИИ: {e}"), 0)

        self.app._executor.submit(work)

    def _show_ai_result(self, text: str) -> None:
        """Показывает результат анализа ИИ."""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.dialog.dialog import (
            MDDialogHeadlineText,
            MDDialogSupportingText,
            MDDialogButtonContainer,
        )
        from kivymd.uix.button import MDButton, MDButtonText

        dialog = MDDialog(
            MDDialogHeadlineText(text="Результат анализа"),
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

    def show_reagent_menu(self) -> None:
        """Показывает меню выбора реагентов над кнопкой."""
        from kivymd.uix.menu import MDDropdownMenu

        menu_items = []
        for key, data in REAGENTS.items():
            menu_items.append({
                "text": data["name"],
                "font_size": sp(12),
                "height": dp(36),
                "on_release": lambda k=key: self._select_reagent(k),
            })

        reagent_btn = self.ids.get("reagent_btn")
        if not reagent_btn:
            return


        menu_width = dp(160)


        max_height = min(dp(300), Window.height * 0.5)

        self._reagent_menu = MDDropdownMenu(
            caller=reagent_btn,
            items=menu_items,
            width=menu_width,
            position="auto",
            max_height=max_height,
        )
        self._reagent_menu.open()

    def _select_reagent(self, reagent_key: str) -> None:
        """Обработка выбора реагента из меню."""
        if hasattr(self, '_reagent_menu') and self._reagent_menu:
            self._reagent_menu.dismiss()
        self.add_reagent(reagent_key)

    def add_reagent(self, reagent_key: str) -> None:
        """Добавляет реагент к молекуле."""
        if reagent_key not in REAGENTS:
            self._show_message("Неизвестный реагент")
            return

        reagent = REAGENTS[reagent_key]


        if self._current_atoms:
            max_x = max(a.x for a in self._current_atoms)
            offset_x = max_x + 3.0
        else:
            offset_x = 0.0


        base_idx = len(self._current_atoms)
        for (element, x, y, z) in reagent["atoms"]:
            new_atom = Atom(element=element, x=x + offset_x, y=y, z=z)
            self._current_atoms.append(new_atom)


        for (i, j) in reagent["bonds"]:
            self._current_bonds.append((base_idx + i, base_idx + j))

            self._highlight_form.append(bond_key(base_idx + i, base_idx + j))

        self._update_viewer()
        self._update_info()


        self._added_reagents.append(reagent_key)


        short_name = reagent_key
        self._show_message(f"+ {short_name}")


        self._reagent_added = True
        self._update_run_button()


        def clear_highlight(*_):
            self._highlight_form = []
            self._update_viewer()
        Clock.schedule_once(clear_highlight, 1.5)

    def apply_heat(self) -> None:
        """Нагрев — устанавливает температуру +50 C от текущей."""
        new_temp = min(500, self._temperature + 50)
        self._temperature = new_temp

        temp_slider = self.ids.get("temp_slider")
        if temp_slider:
            temp_slider.value = new_temp

        self._update_temp_label()
        self._apply_temperature_effect()

        if not self._highlight_break:
            self._show_message(f"Нагрев до {new_temp:.0f} C")

    def apply_cooling(self) -> None:
        """Охлаждение — устанавливает температуру -50 C от текущей."""
        new_temp = max(-200, self._temperature - 50)
        self._temperature = new_temp

        temp_slider = self.ids.get("temp_slider")
        if temp_slider:
            temp_slider.value = new_temp

        self._update_temp_label()
        self._apply_temperature_effect()
        self._show_message(f"Охлаждение до {new_temp:.0f} C")

    def _update_run_button(self) -> None:
        """Показывает/скрывает кнопку 'Запустить процесс'."""
        run_btn = self.ids.get("run_reaction_btn")
        if run_btn:
            if self._reagent_added:
                run_btn.opacity = 1
                run_btn.height = dp(32)
                run_btn.width = dp(172)
                run_btn.disabled = False
            else:
                run_btn.opacity = 0
                run_btn.height = dp(0)
                run_btn.width = dp(0)
                run_btn.disabled = True

    def run_reaction(self) -> None:
        """Запускает химическую реакцию с добавленными реагентами."""
        if not self._reagent_added:
            self._show_message("Сначала добавьте реагент")
            return

        self._show_message("Анализирую реакцию...")


        self._analyze_reaction_with_ai()

    def _analyze_reaction_with_ai(self) -> None:
        """Анализируем реакцию с помощью ИИ и показываем результат с анимацией."""

        base_counts: dict[str, int] = {}
        for a in (self._original_atoms or []):
            base_counts[a.element] = base_counts.get(a.element, 0) + 1

        def _base_key_from_counts(c: dict[str, int]) -> str:
            def same(d):
                return d == c
            if same({"H": 2, "O": 1}):
                return "H2O"
            if same({"H": 1, "Cl": 1}):
                return "HCl"
            if same({"Na": 1, "O": 1, "H": 1}):
                return "NaOH"
            if same({"H": 2, "S": 1, "O": 4}):
                return "H2SO4"
            if same({"H": 1, "N": 1, "O": 3}):
                return "HNO3"
            if same({"N": 1, "H": 3}):
                return "NH3"
            if same({"C": 1, "O": 2}):
                return "CO2"
            if same({"Na": 1, "Cl": 1}):
                return "NaCl"
            if same({"C": 1, "H": 4, "O": 1}):
                return "CH3OH"
            if same({"C": 2, "H": 6, "O": 1}):
                return "C2H5OH"
            if same({"C": 9, "H": 8, "O": 4}):
                return "Aspirin"
            return ""

        base_key = _base_key_from_counts(base_counts)
        reagents_str = " + ".join(([base_key] if base_key else []) + list(self._added_reagents))


        combo = frozenset(([base_key] if base_key else []) + list(self._added_reagents))
        if combo in KNOWN_REACTIONS:
            rule = KNOWN_REACTIONS[combo]
            min_t = float(rule.get("min_temp", 0) or 0)
            if float(self._temperature) >= min_t:
                eq = str(rule.get("equation") or "").strip()
                products = str(rule.get("products") or "").strip()
                descr = str(rule.get("description") or "").strip()
                if eq or products or descr:
                    txt = ""
                    if eq:
                        txt += f"Уравнение: {eq}\n"
                    if products:
                        txt += f"Продукты: {products}\n"
                    if descr:
                        txt += descr
                    Clock.schedule_once(lambda *_: self._run_reaction_animation(txt.strip(), "Химическая реакция"), 0)
                    return

        nav = getattr(self.app, "nav_state", {}) or {}
        base_title = str(nav.get("title") or "").strip()
        base_formula = molecule_formula(list(self._original_atoms or []))

        prompt = (
            f"Исходное вещество: {base_title or 'неизвестно'}; формула: {base_formula}.\n"
            f"Добавили: {', '.join(self._added_reagents) if self._added_reagents else 'ничего'}.\n"
            f"Условия: {self._temperature:.0f} C.\n\n"
            "Задание: объясни, что произойдет при добавлении реагентов к исходному веществу. "
            "Не описывай свойства воды отдельно; отвечай именно про взаимодействие и возможные продукты. "
            "Если реакции нет, так и напиши и объясни что происходит (например растворение, диссоциация, гидролиз).\n"
            "Начни строго с одного из: РЕАКЦИЯ: / СМЕШИВАНИЕ: / НЕВОЗМОЖНО:\n"
            "Дальше: уравнение (если есть), продукты, наблюдения/признаки."
        )

        if not self.app._ai_engine:
            self._show_message("ИИ недоступен. Подключите интернет или скачайте оффлайн-модель.")
            return

        def work():
            try:

                answer = self.app._ai_engine.ask(prompt, verify=True, max_tokens=260)
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
                        lambda *_: self._show_reaction_result(
                            "Не удалось проанализировать эту комбинацию.\n\n"
                            "Попробуйте другие вещества.",
                            title="Ошибка анализа"
                        ), 0
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

                    Clock.schedule_once(
                        lambda *_: self._show_reaction_result(result_text, title=title), 0
                    )

            except Exception as e:
                Logger.exception(f"[MoleculeEditor] AI error: {e}")
                Clock.schedule_once(
                    lambda *_: self._show_message("Ошибка ИИ. Проверьте подключение."), 0
                )

        self.app._executor.submit(work)

    def _run_reaction_animation(self, result_text: str, title: str) -> None:
        """Запускает анимацию реакции и показывает результат."""
        import random

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
                    if dist < 2.5 and len(new_bonds) < 2:
                        self._current_bonds.append(bond)
                        new_bonds.append(bond)

            self._highlight_form = [bond_key(b[0], b[1]) for b in new_bonds]
            self._update_viewer()

        Clock.schedule_once(phase3, 1.5)


        def phase4(*_):
            self._highlight_form = []
            self._highlight_break = []
            self._update_viewer()
            self._show_reaction_result(result_text, title=title)

        Clock.schedule_once(phase4, 2.5)

    def _show_reaction_result(self, text: str, title: str = "Результат реакции") -> None:
        """Показывает результат реакции."""
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


        self._reagent_added = False
        self._added_reagents = []
        self._update_run_button()
