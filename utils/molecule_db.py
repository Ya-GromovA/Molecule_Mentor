# /home/ulyashka_88/molecule-mentor/utils/molecule_db.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from utils.pdb_tools import load_pdb_file, formula_hill, to_subscript


# --- атомные массы для мол. массы (г/моль), школьный уровень ---
ATOMIC_MASS = {
    "H": 1.008,
    "C": 12.011,
    "N": 14.007,
    "O": 15.999,
    "S": 32.06,
    "P": 30.974,
    "F": 18.998,
    "CL": 35.45,
    "BR": 79.904,
    "I": 126.904,
    "NA": 22.990,
    "K": 39.098,
    "MG": 24.305,
    "CA": 40.078,
}


@dataclass(frozen=True)
class MoleculeDef:
    key: str                 # имя файла без .pdb
    name: str                # русское имя
    formula: str             # ASCII: H2O, CH3COOH (для логики)
    atoms: List[str]         # список элементов (H, C, O...) по атомам
    system_name: str = ""    # систематическое/химическое название (опционально)
    formula_pretty: str = "" # красивая формула с индексами (для UI)
    molar_mass: float = 0.0  # молекулярная масса (г/моль)


BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_MOL_DIR = BASE_DIR / "assets" / "molecules"


# key -> (ru_name, system_name, formula_override_ascii)
# Формула override нужна, потому что Hill-сортировка для неорганики даёт некрасиво (CLH вместо HCl, CLNA вместо NaCl).
MOLECULE_DICT: Dict[str, Tuple[str, str, Optional[str]]] = {
    "water": ("Вода", "Оксид водорода", "H2O"),
    "methane": ("Метан", "Тетрагидрид углерода", "CH4"),
    "ammonia": ("Аммиак", "Тригидрид азота", "NH3"),
    "co2": ("Углекислый газ", "Диоксид углерода", "CO2"),
    "oxygen": ("Кислород", "Дикислород", "O2"),
    "nitrogen": ("Азот", "Динитроген", "N2"),
    "hydrogen": ("Водород", "Дигидроген", "H2"),
    "ethane": ("Этан", "Этан", "C2H6"),
    "propane": ("Пропан", "Пропан", "C3H8"),
    "butane": ("Бутан", "Бутан", "C4H10"),
    "ethanol": ("Этанол", "Этиловый спирт", "C2H6O"),
    "acetone": ("Ацетон", "Пропанон", "C3H6O"),
    "benzene": ("Бензол", "Бензен", "C6H6"),
    "phenol": ("Фенол", "Гидроксибензол", "C6H6O"),
    "toluene": ("Толуол", "Метилбензол", "C7H8"),
    "glucose": ("Глюкоза", "D-глюкоза", "C6H12O6"),
    "glycerol": ("Глицерин", "Пропан-1,2,3-триол", "C3H8O3"),
    "urea": ("Мочевина", "Карбамид", "CH4N2O"),
    "glycine": ("Глицин", "Аминоуксусная кислота", "C2H5NO2"),
    "alanine": ("Аланин", "2-аминопропановая кислота", "C3H7NO2"),

    "acetic_acid": ("Уксусная кислота", "Этановая кислота", "C2H4O2"),
    "formic_acid": ("Муравьиная кислота", "Метановая кислота", "CH2O2"),
    "nitric_acid": ("Азотная кислота", "Нитрат водорода", "HNO3"),
    "sulfuric_acid": ("Серная кислота", "Сульфат водорода", "H2SO4"),

    "hcl": ("Хлороводород", "Соляная кислота (в воде)", "HCl"),
    "naoh": ("Гидроксид натрия", "Едкий натр", "NaOH"),
    "nacl": ("Хлорид натрия", "Поваренная соль", "NaCl"),
    "acetylene": ("Ацетилен", "Этин", "C2H2"),
    "ethene": ("Этен (этилен)", "Этен", "C2H4"),
    "formaldehyde": ("Формальдегид", "Метаналь", "CH2O"),
}


def _molar_mass_from_atoms(atoms: List[str]) -> float:
    total = 0.0
    for el in atoms:
        e = str(el).upper()
        total += ATOMIC_MASS.get(e, 0.0)
    return total


def _infer_atoms_and_formula_from_pdb(pdb_path: Path) -> Tuple[List[str], str]:
    atoms_dicts = load_pdb_file(pdb_path)
    elems = [str(a.get("element", "C")).upper() for a in atoms_dicts]
    f = formula_hill(atoms_dicts)  # ASCII, но может быть “CLH”
    return elems, f


def scan_molecules() -> List[MoleculeDef]:
    if not ASSETS_MOL_DIR.exists():
        # если вдруг ассеты не в проекте (крайний случай)
        return []

    mols: List[MoleculeDef] = []
    for pdb in sorted(ASSETS_MOL_DIR.glob("*.pdb")):
        key = pdb.stem

        atoms, formula_guess = _infer_atoms_and_formula_from_pdb(pdb)

        ru_name = key
        system = ""
        formula = formula_guess

        if key in MOLECULE_DICT:
            ru_name, system, override = MOLECULE_DICT[key]
            if override:
                formula = override

        formula_pretty = to_subscript(formula)
        mm = _molar_mass_from_atoms(atoms)

        mols.append(
            MoleculeDef(
                key=key,
                name=ru_name,
                formula=formula,
                atoms=[a.upper() for a in atoms],
                system_name=system,
                formula_pretty=formula_pretty,
                molar_mass=mm,
            )
        )

    return mols


# Главный список — теперь из автоскана
MOLECULES: List[MoleculeDef] = scan_molecules()

# Индексы
KEY_INDEX: Dict[str, MoleculeDef] = {m.key: m for m in MOLECULES}
NAME_INDEX: Dict[str, MoleculeDef] = {m.name.lower(): m for m in MOLECULES}
FORMULA_INDEX: Dict[str, MoleculeDef] = {m.formula: m for m in MOLECULES}
