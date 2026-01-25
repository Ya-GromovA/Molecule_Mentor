from __future__ import annotations

import random
from pathlib import Path
from typing import Optional

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen

from kivymd.uix.label import MDLabel

from utils.chem_types import Atom, bond_key, molecular_mass
from utils.molecule_parser import MoleculeParseError, molecule_formula, parse_pdb
from utils.visualizer_3d import Visualizer3D


# реагенты для добавления
REAGENTS = {
    "HCl": {"name": "Соляная кислота (HCl)", "atoms": [("H", 0, 0, 0), ("Cl", 1.3, 0, 0)], "bonds": [(0, 1)]},
    "H2SO4": {"name": "Серная кислота (H2SO4)", "atoms": [("S", 0, 0, 0), ("O", 1.4, 0, 0), ("O", -1.4, 0, 0), ("O", 0, 1.4, 0), ("O", 0, -1.4, 0), ("H", 0, 2.4, 0), ("H", 0, -2.4, 0)], "bonds": [(0, 1), (0, 2), (0, 3), (0, 4), (3, 5), (4, 6)]},
    "HNO3": {"name": "Азотная кислота (HNO3)", "atoms": [("N", 0, 0, 0), ("O", 1.2, 0, 0), ("O", -0.6, 1.0, 0), ("O", -0.6, -1.0, 0), ("H", -1.5, 1.0, 0)], "bonds": [(0, 1), (0, 2), (0, 3), (2, 4)]},
    "NaOH": {"name": "Гидроксид натрия (NaOH)", "atoms": [("Na", 0, 0, 0), ("O", 2.0, 0, 0), ("H", 3.0, 0, 0)], "bonds": [(0, 1), (1, 2)]},
    "H2O": {"name": "Вода (H2O)", "atoms": [("O", 0, 0, 0), ("H", 0.96, 0, 0), ("H", -0.24, 0.93, 0)], "bonds": [(0, 1), (0, 2)]},
    "NH3": {"name": "Аммиак (NH3)", "atoms": [("N", 0, 0, 0), ("H", 1.0, 0, 0), ("H", -0.5, 0.87, 0), ("H", -0.5, -0.87, 0)], "bonds": [(0, 1), (0, 2), (0, 3)]},
    "CH3OH": {"name": "Метанол (CH3OH)", "atoms": [("C", 0, 0, 0), ("O", 1.4, 0, 0), ("H", 1.9, 0.8, 0), ("H", -0.6, 0.9, 0), ("H", -0.6, -0.9, 0), ("H", 0, 0, 1.0)], "bonds": [(0, 1), (1, 2), (0, 3), (0, 4), (0, 5)]},
    "CO2": {"name": "Углекислый газ (CO2)", "atoms": [("C", 0, 0, 0), ("O", 1.2, 0, 0), ("O", -1.2, 0, 0)], "bonds": [(0, 1), (0, 2)]},
}

# база известных реакций
# формат: {reagents_set: {"possible": bool, "min_temp": int, "equation": str, "products": str, "description": str}}
KNOWN_REACTIONS = {
    # кислота + основание -> соль + вода (нейтрализация)
    frozenset(["HCl", "NaOH"]): {
        "possible": True,
        "min_temp": -50,  # идёт почти при любой температуре
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
    # кислота + спирт -> эфир + вода (этерификация)
    frozenset(["CH3OH", "HCl"]): {
        "possible": True,
        "min_temp": 50,  # нужна температура
        "equation": "CH3OH + HCl -> CH3Cl + H2O",
        "products": "хлорметан (метилхлорид) и вода",
        "description": "Реакция замещения гидроксильной группы на хлор. Требует нагревания.",
    },
    # аммиак + кислота -> соль аммония
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
    # вода + ... (обычно без катализатора не реагирует)
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
    # метанол + вода - не реагируют, просто смешиваются
    frozenset(["CH3OH", "H2O"]): {
        "possible": False,
        "min_temp": 0,
        "equation": "",
        "products": "",
        "description": "Метанол и вода не вступают в химическую реакцию. Они лишь смешиваются в любых пропорциях (оба — полярные растворители).",
    },
}


class MoleculeEditorScreen(Screen):
    # редактор молекул: можно удалять атомы, добавлять связи и реагенты

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._viewer: Optional[Visualizer3D] = None
        self._original_atoms: list[Atom] = []
        self._original_bonds: list[tuple[int, int]] = []
        self._current_atoms: list[Atom] = []
        self._current_bonds: list[tuple[int, int]] = []
        self._highlight_break: list[tuple[int, int]] = []
        self._highlight_form: list[tuple[int, int]] = []
        
        self._temperature: float = 25.0  # температура в градусах
        self._message_label: Optional[MDLabel] = None
        self._temp_label: Optional[MDLabel] = None
        self._selected_reagent: Optional[str] = None
        
        # режим создания связей (если False - удаляем)
        self._bond_mode: bool = False
        self._first_atom_idx: Optional[int] = None
        
        # список добавленных реагентов
        self._added_reagents: list[str] = []
        
        # флаг для кнопки "Запустить"
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

        # контейнер для 3D-вьювера
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
        # включаем режим редактирования
        self._viewer.edit_mode = True
        self._viewer.on_atom_tap = self._on_atom_tap
        self._viewer.on_bond_tap = self._on_bond_tap
        
        card.add_widget(self._viewer)
        host.add_widget(card)

        # сбрасываем температуру и флаги
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
        
        # режим создания связей
        if self._bond_mode:
            self._handle_bond_mode_tap(atom_idx)
            return
        
        # режим удаления (по умолчанию)
        atom = self._current_atoms[atom_idx]
        element = atom.element
        
        # удаляем атом и все его связи
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
            # первый атом выбран
            self._first_atom_idx = atom_idx
            atom = self._current_atoms[atom_idx]
            self._show_message(f"Выбран {atom.element}. Тапните второй атом")
        else:
            # второй атом выбран - создаём связь
            if self._first_atom_idx == atom_idx:
                self._show_message("Нельзя связать атом с самим собой")
                self._first_atom_idx = None
                return
            
            # проверяем, нет ли уже такой связи
            bond = (min(self._first_atom_idx, atom_idx), max(self._first_atom_idx, atom_idx))
            if bond in self._current_bonds:
                self._show_message("Связь уже существует")
                self._first_atom_idx = None
                return
            
            # создаём связь
            self._current_bonds.append(bond)
            self._highlight_form.append(bond_key(bond[0], bond[1]))
            
            a1 = self._current_atoms[self._first_atom_idx]
            a2 = self._current_atoms[atom_idx]
            self._show_message(f"Связь {a1.element}-{a2.element} создана")
            
            self._first_atom_idx = None
            self._update_viewer()
            self._update_info()
            
            # убираем подсветку через 1.5 секунды
            def clear_highlight(*_):
                self._highlight_form = []
                self._update_viewer()
            Clock.schedule_once(clear_highlight, 1.5)

    def _on_bond_tap(self, bond: tuple[int, int]) -> None:
        """Обработка тапа по связи — удаление (в режиме удаления)."""
        if self._bond_mode:
            # в режиме связывания тап по связи ничего не делает
            return
        
        # режим удаления
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
            temp_label.text = f"{self._temperature:.0f}°C"

    def _show_message(self, text: str) -> None:
        """Показывает сообщение в UI."""
        msg_label = self.ids.get("message_label")
        if msg_label:
            msg_label.text = text
            # очищаем через 3 секунды
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
        
        # нормализуем температуру: -200..500 -> 0..1
        t = (self._temperature + 200) / 700  # 0 = -200°C, 1 = 500°C
        
        # цвет по температуре: синий -> белый -> красный
        if t < 0.32:  # холодно (-200 до ~25°C)
            # синий -> белый
            ratio = t / 0.32
            r = 0.2 + ratio * 0.8
            g = 0.5 + ratio * 0.5
            b = 0.95
        else:  # тепло/жарко (>25°C)
            # белый -> красный
            ratio = (t - 0.32) / 0.68
            r = 0.95
            g = 1.0 - ratio * 0.7
            b = 1.0 - ratio * 0.8
        
        color = (r, g, b, 1)
        
        # цвет трека слайдера
        try:
            temp_slider.track_active_color = color
            temp_slider.thumb_color = color
        except Exception:
            pass  # если свойства не поддерживаются
        
        # цвет лейбла температуры
        if temp_label:
            temp_label.text_color = color

    def _apply_temperature_effect(self) -> None:
        """Применяет эффект температуры к молекуле."""
        if not self._current_bonds:
            return
        
        # при высокой температуре (>100°C) есть шанс разрыва связи
        if self._temperature > 100:
            break_chance = (self._temperature - 100) / 500  # 0-0.8 при 100-500°C
            if random.random() < break_chance and self._current_bonds:
                # выбираем случайную связь
                bond_idx = random.randint(0, len(self._current_bonds) - 1)
                broken = self._current_bonds.pop(bond_idx)
                self._highlight_break.append(bond_key(broken[0], broken[1]))
                self._update_viewer()
                self._update_info()
                self._show_message(f"Связь разорвана при {self._temperature:.0f}°C!")
        
        # при очень низкой температуре (<-50°C) молекула "замерзает"
        elif self._temperature < -50:
            self._show_message(f"Молекула заморожена при {self._temperature:.0f}°C")

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
            # текст показывает что можно сделать
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
        
        # обновляем слайдер
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
        """Определение молекулы с помощью ИИ."""
        if not self._current_atoms:
            self._show_message("Нет атомов для анализа")
            return

        formula = molecule_formula(self._current_atoms)
        
        # считаем атомы для более детального анализа
        atom_counts: dict[str, int] = {}
        for atom in self._current_atoms:
            atom_counts[atom.element] = atom_counts.get(atom.element, 0) + 1
        atom_list = ", ".join(f"{el}: {cnt}" for el, cnt in sorted(atom_counts.items()))
        
        prompt = (
            f"Проанализируй химическую структуру с формулой {formula} (атомы: {atom_list}). "
            f"Это может быть смесь нескольких молекул или продукт реакции. "
            f"Варианты ответа:\n"
            f"1. Если это одна известная молекула — назови её (русское название), класс соединения и применение.\n"
            f"2. Если это смесь молекул (например, глицерин + вода) — определи компоненты и опиши возможную реакцию между ними.\n"
            f"3. Если структура химически невозможна — объясни почему.\n"
            f"Ответь кратко (3-4 предложения)."
        )

        if not self.app._ai_engine:
            self._show_message("ИИ недоступен")
            return

        self._show_message("Анализирую...")

        def work():
            try:
                # verify=False - отключаем верификатор для коротких запросов
                answer = self.app._ai_engine.ask(prompt, verify=False)
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
        """Показывает меню выбора реагентов."""
        from kivymd.uix.menu import MDDropdownMenu
        
        menu_items = []
        for key, data in REAGENTS.items():
            menu_items.append({
                "text": data["name"],
                "on_release": lambda k=key: self._select_reagent(k),
            })
        
        reagent_btn = self.ids.get("reagent_btn")
        if not reagent_btn:
            return
        
        self._reagent_menu = MDDropdownMenu(
            caller=reagent_btn,
            items=menu_items,
            width=min(dp(320), Window.width - dp(24)),
            position="center",
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
        
        # считаем смещение для нового реагента
        if self._current_atoms:
            max_x = max(a.x for a in self._current_atoms)
            offset_x = max_x + 3.0
        else:
            offset_x = 0.0
        
        # добавляем атомы реагента
        base_idx = len(self._current_atoms)
        for (element, x, y, z) in reagent["atoms"]:
            new_atom = Atom(element=element, x=x + offset_x, y=y, z=z)
            self._current_atoms.append(new_atom)
        
        # добавляем связи реагента
        for (i, j) in reagent["bonds"]:
            self._current_bonds.append((base_idx + i, base_idx + j))
            # подсвечиваем новые связи
            self._highlight_form.append(bond_key(base_idx + i, base_idx + j))
        
        self._update_viewer()
        self._update_info()
        
        # запоминаем добавленный реагент
        self._added_reagents.append(reagent_key)
        
        # короткое имя реагента
        short_name = reagent_key
        self._show_message(f"+ {short_name}")
        
        # показываем кнопку "Запустить процесс"
        self._reagent_added = True
        self._update_run_button()
        
        # убираем подсветку через 1.5 секунды
        def clear_highlight(*_):
            self._highlight_form = []
            self._update_viewer()
        Clock.schedule_once(clear_highlight, 1.5)

    def apply_heat(self) -> None:
        """Нагрев — устанавливает температуру +50°C от текущей."""
        new_temp = min(500, self._temperature + 50)
        self._temperature = new_temp
        
        temp_slider = self.ids.get("temp_slider")
        if temp_slider:
            temp_slider.value = new_temp
        
        self._update_temp_label()
        self._apply_temperature_effect()
        
        if not self._highlight_break:
            self._show_message(f"Нагрев до {new_temp:.0f}°C")

    def apply_cooling(self) -> None:
        """Охлаждение — устанавливает температуру -50°C от текущей."""
        new_temp = max(-200, self._temperature - 50)
        self._temperature = new_temp
        
        temp_slider = self.ids.get("temp_slider")
        if temp_slider:
            temp_slider.value = new_temp
        
        self._update_temp_label()
        self._apply_temperature_effect()
        self._show_message(f"Охлаждение до {new_temp:.0f}°C")

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
        
        # проверяем, есть ли известная реакция в базе
        reagent_set = frozenset(self._added_reagents)
        known = KNOWN_REACTIONS.get(reagent_set)
        
        if known:
            # известная реакция - проверяем условия
            self._run_known_reaction(known)
        else:
            # неизвестная комбинация - спрашиваем ИИ
            self._run_unknown_reaction()
    
    def _run_known_reaction(self, reaction_info: dict) -> None:
        """Запускает известную реакцию с визуализацией."""
        possible = reaction_info["possible"]
        min_temp = reaction_info.get("min_temp", -273)
        equation = reaction_info.get("equation", "")
        products = reaction_info.get("products", "")
        description = reaction_info.get("description", "")
        
        if not possible:
            # реакция невозможна - показываем сообщение без анимации
            self._show_reaction_result(
                f"Реакция невозможна.\n\n{description}",
                title="Реакция не идёт"
            )
            return
        
        if self._temperature < min_temp:
        # температура слишком низкая
            self._show_reaction_result(
                f"Реакция возможна, но требует температуры выше {min_temp}°C.\n"
                f"Текущая температура: {self._temperature:.0f}°C.\n\n"
                f"Увеличьте температуру и попробуйте снова.",
                title="Недостаточная температура"
            )
            return
        
        # реакция идёт - запускаем анимацию
        self._show_message("Реакция идёт!")
        self._animate_reaction(equation, products, description)
    
    def _animate_reaction(self, equation: str, products: str, description: str) -> None:
        """Анимация реакции: разрыв связей, перегруппировка, образование новых связей."""
        # фаза 1: подсветка разрывающихся связей (красным)
        if self._current_bonds:
            # выбираем случайные связи для разрыва (30-50% связей)
            import random
            num_to_break = max(1, len(self._current_bonds) // 3)
            bonds_to_break = random.sample(self._current_bonds, min(num_to_break, len(self._current_bonds)))
            
            self._highlight_break = [bond_key(b[0], b[1]) for b in bonds_to_break]
            self._update_viewer()
        
        # фаза 2: через 0.8 сек удаляем разорванные связи
        def phase2(*_):
            for b in list(self._highlight_break):
                # удаляем связь из текущих
                bond = b if b in self._current_bonds else (b[1], b[0])
                if bond in self._current_bonds:
                    self._current_bonds.remove(bond)
                elif (bond[1], bond[0]) in self._current_bonds:
                    self._current_bonds.remove((bond[1], bond[0]))
            
            self._highlight_break = []
            self._update_viewer()
            self._update_info()
        
        Clock.schedule_once(phase2, 0.8)
        
        # фаза 3: через 1.5 сек образуем новые связи (зелёным)
        def phase3(*_):
            # ищем близкие атомы без связей и соединяем
            new_bonds_formed = []
            for i, atom_i in enumerate(self._current_atoms):
                for j, atom_j in enumerate(self._current_atoms):
                    if i >= j:
                        continue
                    # проверяем, нет ли уже связи
                    bond = (min(i, j), max(i, j))
                    if bond in self._current_bonds:
                        continue
                    
                    # считаем расстояние
                    dist = ((atom_i.x - atom_j.x)**2 + (atom_i.y - atom_j.y)**2 + (atom_i.z - atom_j.z)**2) ** 0.5
                    
                    # если атомы близко (< 2.5 ангстрем) - создаём связь
                    if dist < 2.5 and len(new_bonds_formed) < 3:
                        self._current_bonds.append(bond)
                        new_bonds_formed.append(bond)
            
            # подсвечиваем новые связи
            self._highlight_form = [bond_key(b[0], b[1]) for b in new_bonds_formed]
            self._update_viewer()
            self._update_info()
        
        Clock.schedule_once(phase3, 1.5)
        
        # фаза 4: через 2.5 сек показываем результат
        def phase4(*_):
            self._highlight_form = []
            self._highlight_break = []
            self._update_viewer()
            
            result_text = f"Уравнение: {equation}\n\nПродукты: {products}\n\n{description}"
            self._show_reaction_result(result_text, title="Реакция прошла!")
        
        Clock.schedule_once(phase4, 2.5)
    
    def _run_unknown_reaction(self) -> None:
        """Спрашиваем ИИ о неизвестной реакции."""
        formula = molecule_formula(self._current_atoms)
        
        # считаем атомы
        atom_counts: dict[str, int] = {}
        for atom in self._current_atoms:
            atom_counts[atom.element] = atom_counts.get(atom.element, 0) + 1
        atom_list = ", ".join(f"{el}: {cnt}" for el, cnt in sorted(atom_counts.items()))
        
        reagents_str = " + ".join(self._added_reagents)
        
        prompt = (
            f"Вопрос: возможна ли химическая реакция между {reagents_str} при {self._temperature:.0f}°C?\n\n"
            f"Если ты НЕ ЗНАЕШЬ или НЕ УВЕРЕН — напиши: 'Данных недостаточно'.\n"
            f"Если реакция НЕВОЗМОЖНА — напиши: 'Реакция невозможна' и объясни почему.\n"
            f"Если реакция ВОЗМОЖНА — напиши по пунктам:\n"
            f"1. Уравнение реакции (например: HCl + NaOH -> NaCl + H2O)\n"
            f"2. Что получается (названия продуктов на русском)\n"
            f"3. Что происходит (выделяется тепло/газ, выпадает осадок, меняется цвет и т.д.)\n"
            f"4. Тип реакции (нейтрализация, замещение, присоединение и т.д.)\n"
            f"5. Интересный факт или применение этой реакции\n\n"
            f"Ответь понятно и информативно. Не повторяй текст."
        )
        
        if not self.app._ai_engine:
            self._show_message("ИИ недоступен")
            return
        
        def work():
            try:
                answer = self.app._ai_engine.ask(prompt, verify=False)
                
                # проверяем качество ответа
                answer_lower = answer.lower()
                
                # признаки что ИИ не знает ответа
                is_unknown = (
                    "не знаю" in answer_lower or
                    "недостаточно" in answer_lower or
                    "не уверен" in answer_lower or
                    "неизвестно" in answer_lower or
                    "не могу определить" in answer_lower or
                    len(answer.strip()) < 20
                )
                
                # признаки повторяющегося текста (галлюцинация)
                words = answer.split()
                if len(words) > 20:
                    # проверяем, есть ли повторяющиеся фразы
                    phrase_counts = {}
                    for i in range(len(words) - 4):
                        phrase = " ".join(words[i:i+5])
                        phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
                    if any(count > 2 for count in phrase_counts.values()):
                        is_unknown = True
                
                # определяем результат
                if is_unknown:
                    title = "Результат неизвестен"
                    result_text = (
                        "Не удалось определить результат этой реакции.\n\n"
                        "Попробуйте другую комбинацию реагентов или "
                        "используйте известные реакции (кислота + основание, и т.д.)."
                    )
                elif "невозможна" in answer_lower:
                    title = "Реакция невозможна"
                    result_text = answer
                elif (
                    "возможна" in answer_lower or 
                    "->" in answer or
                    "образуется" in answer_lower or
                    "получается" in answer_lower
                ):
                    title = "Реакция возможна"
                    result_text = answer
                    # показываем анимацию только для возможных реакций
                    Clock.schedule_once(lambda *_: self._simple_reaction_animation(), 0)
                else:
                    title = "Результат анализа"
                    result_text = answer
                
                def show_result(*_):
                    delay = 1.5 if title == "Реакция возможна" else 0
                    if delay > 0:
                        Clock.schedule_once(
                            lambda *_: self._show_reaction_result(result_text, title=title),
                            delay
                        )
                    else:
                        self._show_reaction_result(result_text, title=title)
                
                Clock.schedule_once(show_result, 0)
            except Exception as e:
                Logger.exception(f"[MoleculeEditor] AI error: {e}")
                Clock.schedule_once(lambda *_: self._show_message(f"Ошибка: {e}"), 0)
        
        self.app._executor.submit(work)
    
    def _simple_reaction_animation(self) -> None:
        """Простая анимация для неизвестных реакций."""
        import random
        
        if not self._current_bonds:
            return
        
        # разрываем 1-2 случайные связи
        num_to_break = min(2, len(self._current_bonds))
        bonds_to_break = random.sample(self._current_bonds, num_to_break)
        
        self._highlight_break = [bond_key(b[0], b[1]) for b in bonds_to_break]
        self._update_viewer()
        
        def remove_bonds(*_):
            for b in bonds_to_break:
                if b in self._current_bonds:
                    self._current_bonds.remove(b)
                elif (b[1], b[0]) in self._current_bonds:
                    self._current_bonds.remove((b[1], b[0]))
            self._highlight_break = []
            self._update_viewer()
            self._update_info()
        
        Clock.schedule_once(remove_bonds, 0.6)

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
        
        # сбрасываем флаги
        self._reagent_added = False
        self._added_reagents = []
        self._update_run_button()
