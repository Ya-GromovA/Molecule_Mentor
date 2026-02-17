from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional

from .chem_types import Atom


@dataclass
class MoleculeState:
    atoms: list[Atom]
    bonds: list[tuple[int, int]]


def heat_transform(state: MoleculeState, intensity: float) -> tuple[MoleculeState, list[tuple[int, int]]]:
    """
    "Нагрев": реально меняем структуру — рвём часть связей.
    Эвристика: рвём самые длинные связи (как "слабее" по расстоянию) + чуть рандома.
    Returns: new state, broken bonds
    """
    atoms = state.atoms
    bonds = list(state.bonds)
    if not atoms or not bonds:
        return state, []

    def bond_len(b):
        i, j = b
        ai = atoms[i]
        aj = atoms[j]
        return math.dist((ai.x, ai.y, ai.z), (aj.x, aj.y, aj.z))

    bonds_sorted = sorted(bonds, key=bond_len, reverse=True)

    k = int(max(1, min(len(bonds), round(len(bonds) * (0.10 + 0.25 * intensity)))))
    candidates = bonds_sorted[: max(k, 1)]

    broken = set()
    for b in candidates:
        if random.random() < 0.75 + 0.20 * intensity:
            broken.add(tuple(sorted(b)))

    new_bonds = [b for b in bonds if tuple(sorted(b)) not in broken]
    return MoleculeState(atoms=list(atoms), bonds=new_bonds), sorted(broken)


def cool_transform(state: MoleculeState, intensity: float) -> tuple[MoleculeState, list[tuple[int, int]]]:
    """
    "Охлаждение": реально меняем структуру — пробуем сформировать новые связи между ближайшими атомами,
    если они не связаны и находятся достаточно близко.
    Returns: new state, formed bonds
    """
    atoms = state.atoms
    bonds = set(tuple(sorted(b)) for b in state.bonds)
    if len(atoms) < 2:
        return state, []

    formed: set[tuple[int, int]] = set()

    thresh = 1.05 + 0.35 * intensity


    indices = list(range(len(atoms)))
    random.shuffle(indices)

    def dist(i, j):
        ai = atoms[i]
        aj = atoms[j]
        return math.dist((ai.x, ai.y, ai.z), (aj.x, aj.y, aj.z))

    attempts = min(120, len(atoms) * 8)
    for _ in range(attempts):
        i = random.choice(indices)
        j = random.choice(indices)
        if i == j:
            continue
        a, b = (i, j) if i < j else (j, i)
        if (a, b) in bonds or (a, b) in formed:
            continue
        if dist(a, b) <= thresh:
            formed.add((a, b))
            if len(formed) >= max(1, int(1 + 2 * intensity)):
                break

    new_bonds = sorted(bonds.union(formed))
    return MoleculeState(atoms=list(atoms), bonds=new_bonds), sorted(formed)
