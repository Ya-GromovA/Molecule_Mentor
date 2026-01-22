from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple


@dataclass(frozen=True)
class Atom:
    element: str
    x: float
    y: float
    z: float
    label: str = ""


@dataclass(frozen=True)
class Molecule:
    name: str
    atoms: list[Atom]
    bonds: list[tuple[int, int]]  # indices into atoms


@dataclass(frozen=True)
class ReactionMeta:
    reaction_id: str
    name: str
    equation: str
    category: str
    fps: int


@dataclass(frozen=True)
class ReactionFrame:
    atoms: list[Atom]
    bonds: list[tuple[int, int]]
    highlight_break: list[tuple[int, int]]
    highlight_form: list[tuple[int, int]]
    stage_index: int


@dataclass(frozen=True)
class Reaction:
    meta: ReactionMeta
    steps: list[dict]  # {"title":..., "description":...}
    frames: list[ReactionFrame]


ATOMIC_MASS: dict[str, float] = {
    "H": 1.008,
    "C": 12.011,
    "N": 14.007,
    "O": 15.999,
    "F": 18.998,
    "P": 30.974,
    "S": 32.06,
    "Cl": 35.45,
    "Br": 79.904,
    "I": 126.90447,
    "Na": 22.989769,
    "K": 39.0983,
    "Mg": 24.305,
    "Ca": 40.078,
    "Fe": 55.845,
    "Cu": 63.546,
    "Zn": 65.38,
    "Ag": 107.8682,
}


def normalize_element(raw: str) -> str:
    """
    Normalize element symbol from PDB-like sources:
    - trims spaces
    - supports 'CL'/'cl' -> 'Cl'
    - supports single-letter uppercase
    """
    s = (raw or "").strip()
    if not s:
        return "X"
    if len(s) == 1:
        return s.upper()
    # first letter uppercase, rest lowercase (Cl, Na, Mg)
    return s[0].upper() + s[1:].lower()


def atomic_mass(element: str, default: float = 0.0) -> float:
    el = normalize_element(element)
    return float(ATOMIC_MASS.get(el, default))


def molecular_mass(atoms: Iterable[Atom]) -> float:
    """
    Returns molar mass approximation as sum of atomic masses.
    Unknown elements contribute 0.0.
    """
    total = 0.0
    for a in atoms:
        total += atomic_mass(a.element, default=0.0)
    return total


def bond_key(i: int, j: int) -> tuple[int, int]:
    """
    Canonical bond key for undirected bonds.
    """
    return (i, j) if i <= j else (j, i)


def dedupe_bonds(bonds: Iterable[Tuple[int, int]]) -> list[tuple[int, int]]:
    """
    Removes duplicates and self-bonds, returns sorted canonical list.
    """
    s: set[tuple[int, int]] = set()
    for i, j in bonds:
        if i == j:
            continue
        s.add(bond_key(int(i), int(j)))
    return sorted(s)
