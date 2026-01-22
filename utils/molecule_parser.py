from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable

from .chem_types import Atom, Molecule


class MoleculeParseError(RuntimeError):
    pass


def _safe_element(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return "C"
    # normalize (e.g. "CL" -> "Cl")
    if len(raw) == 1:
        return raw.upper()
    return raw[0].upper() + raw[1:].lower()


def parse_pdb(path: str) -> Molecule:
    if not os.path.exists(path):
        raise MoleculeParseError(f"PDB not found: {path}")

    atoms: list[Atom] = []
    bonds: set[tuple[int, int]] = set()

    # PDB: HETATM/ATOM lines and CONECT lines
    # We rely on serial number mapping to atom index
    serial_to_index: dict[int, int] = {}

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            rec = line[:6].strip().upper()
            if rec in ("ATOM", "HETATM"):
                # Example:
                # HETATM    1  C1  UNL     1      -0.994  -0.074  -0.021  1.00  0.00           C
                try:
                    serial = int(line[6:11].strip())
                except Exception:
                    continue

                label = line[12:16].strip()
                try:
                    x = float(line[30:38].strip())
                    y = float(line[38:46].strip())
                    z = float(line[46:54].strip())
                except Exception as e:
                    raise MoleculeParseError(f"Bad coords in {path}: {line!r}") from e

                element = _safe_element(line[76:78].strip() if len(line) >= 78 else "")
                if not element:
                    # fallback from label like "C1"
                    element = _safe_element("".join([c for c in label if c.isalpha()])[:2])

                idx = len(atoms)
                atoms.append(Atom(element=element, x=x, y=y, z=z, label=label or f"{element}{serial}"))
                serial_to_index[serial] = idx

            elif rec == "CONECT":
                # CONECT    1    2    5    6    7
                parts = line.split()
                if len(parts) < 3:
                    continue
                try:
                    a_serial = int(parts[1])
                except Exception:
                    continue
                if a_serial not in serial_to_index:
                    continue
                a_idx = serial_to_index[a_serial]
                for p in parts[2:]:
                    try:
                        b_serial = int(p)
                    except Exception:
                        continue
                    if b_serial not in serial_to_index:
                        continue
                    b_idx = serial_to_index[b_serial]
                    if a_idx == b_idx:
                        continue
                    i, j = (a_idx, b_idx) if a_idx < b_idx else (b_idx, a_idx)
                    bonds.add((i, j))

    if not atoms:
        raise MoleculeParseError(f"No atoms parsed from {path}")

    name = os.path.splitext(os.path.basename(path))[0]
    return Molecule(name=name, atoms=atoms, bonds=sorted(bonds))


def molecule_formula(atoms: list[Atom]) -> str:
    counts: dict[str, int] = {}
    for a in atoms:
        counts[a.element] = counts.get(a.element, 0) + 1

    # Hill system: C then H then alphabetical
    parts: list[tuple[str, int]] = []
    if "C" in counts:
        parts.append(("C", counts.pop("C")))
    if "H" in counts:
        parts.append(("H", counts.pop("H")))
    for el in sorted(counts.keys()):
        parts.append((el, counts[el]))

    def fmt(el: str, n: int) -> str:
        return el if n == 1 else f"{el}{n}"

    return "".join(fmt(el, n) for el, n in parts)
