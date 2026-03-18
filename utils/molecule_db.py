
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from utils.pdb_tools import load_pdb_file, formula_hill, to_subscript
except Exception:
    import re

    _EL_RE = re.compile(r"^[A-Z][a-z]?$")

    def _norm_el(raw: str) -> str:
        s = str(raw or "").strip()
        if not s:
            return ""
        s = s[:2]
        s = s[0].upper() + (s[1:].lower() if len(s) > 1 else "")
        return s if _EL_RE.fullmatch(s) else ""

    def load_pdb_file(pdb_path: Path) -> List[Dict[str, str]]:
        atoms: List[Dict[str, str]] = []
        p = Path(str(pdb_path))
        if not p.exists():
            return atoms
        with p.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not (line.startswith("ATOM") or line.startswith("HETATM")):
                    continue
                el = ""
                if len(line) >= 78:
                    el = _norm_el(line[76:78])
                if not el:
                    parts = line.split()
                    if parts:
                        el = _norm_el(parts[-1])
                if el:
                    atoms.append({"element": el})
        return atoms

    def formula_hill(atoms_dicts: List[Dict[str, str]]) -> str:
        counts: Dict[str, int] = {}
        for atom in atoms_dicts:
            el = _norm_el(str(atom.get("element", "")))
            if not el:
                continue
            counts[el] = counts.get(el, 0) + 1
        if not counts:
            return ""

        parts: List[str] = []
        if "C" in counts:
            c = counts.pop("C")
            parts.append(f"C{c if c > 1 else ''}")
            if "H" in counts:
                h = counts.pop("H")
                parts.append(f"H{h if h > 1 else ''}")
        for el in sorted(counts.keys()):
            n = counts[el]
            parts.append(f"{el}{n if n > 1 else ''}")
        return "".join(parts)

    def to_subscript(formula: str) -> str:
        return str(formula or "")



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
    key: str
    name: str
    formula: str
    atoms: List[str]
    system_name: str = ""
    formula_pretty: str = ""
    molar_mass: float = 0.0


BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_MOL_DIR = BASE_DIR / "assets" / "molecules"




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
    f = formula_hill(atoms_dicts)
    return elems, f


def scan_molecules() -> List[MoleculeDef]:
    if not ASSETS_MOL_DIR.exists():

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



MOLECULES: List[MoleculeDef] = scan_molecules()


KEY_INDEX: Dict[str, MoleculeDef] = {m.key: m for m in MOLECULES}
NAME_INDEX: Dict[str, MoleculeDef] = {m.name.lower(): m for m in MOLECULES}
FORMULA_INDEX: Dict[str, MoleculeDef] = {m.formula: m for m in MOLECULES}


def _formula_canon(value: str) -> str:
    return "".join(str(value or "").split()).upper()


def _title_from_key(key: str) -> str:
    txt = str(key or "").strip().replace("_", " ")
    if not txt:
        return "Молекула"
    return txt.capitalize()


def _catalog_name_fallback(key: str) -> str:
    k = str(key or "").strip().lower()
    if not k:
        return ""
    try:
        from screens.molecules_screen import _MOLECULE_DATA

        name = str((_MOLECULE_DATA.get(k, ("", ""))[0] or "")).strip()
        if name:
            return name
    except Exception:
        pass
    return ""


def resolve_name_formula(key: str = "", pdb_path: Optional[Path] = None) -> Tuple[str, str]:
    k = str(key or "").strip().lower()
    ru_name = ""
    formula = ""

    mol = KEY_INDEX.get(k)
    if mol is not None:
        ru_name = str(getattr(mol, "name", "") or "").strip()
        formula = str(getattr(mol, "formula", "") or "").strip()

    if not formula and pdb_path is not None:
        try:
            atoms_dicts = load_pdb_file(Path(str(pdb_path)))
            formula = str(formula_hill(atoms_dicts) or "").strip()
        except Exception:
            pass

    fallback_name = _catalog_name_fallback(k)
    if fallback_name:
        if not ru_name:
            ru_name = fallback_name
        elif ru_name.strip().lower() == k:
            ru_name = fallback_name

    if not ru_name:
        ru_name = _title_from_key(k)

    return ru_name, formula


def resolve_name_by_formula(formula: str) -> str:
    raw = str(formula or "").strip()
    if not raw:
        return ""

    mol = FORMULA_INDEX.get(raw)
    if mol is not None:
        return str(getattr(mol, "name", "") or "").strip()

    canon = _formula_canon(raw)
    if not canon:
        return ""
    for f_key, f_mol in FORMULA_INDEX.items():
        if _formula_canon(f_key) == canon:
            return str(getattr(f_mol, "name", "") or "").strip()
    return ""
