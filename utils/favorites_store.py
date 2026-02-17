from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Set, Dict, Any


@dataclass
class Favorites:
    molecules: Set[str]
    reactions: Set[str]


def _default() -> Favorites:
    return Favorites(molecules=set(), reactions=set())


def load_favorites(path: str) -> Favorites:
    p = Path(path)
    if not p.exists():
        return _default()

    try:
        raw = json.loads(p.read_text(encoding="utf-8") or "{}")
    except Exception:
        return _default()

    mol = raw.get("molecules") or []
    rxn = raw.get("reactions") or []
    try:
        return Favorites(molecules=set(str(x) for x in mol), reactions=set(str(x) for x in rxn))
    except Exception:
        return _default()


def save_favorites(path: str, fav: Favorites) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    data: Dict[str, Any] = {
        "molecules": sorted(fav.molecules),
        "reactions": sorted(fav.reactions),
    }

    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
    tmp.replace(p)


def toggle_molecule(path: str, molecule_key: str) -> bool:
    fav = load_favorites(path)
    k = str(molecule_key)
    if k in fav.molecules:
        fav.molecules.remove(k)
        save_favorites(path, fav)
        return False
    fav.molecules.add(k)
    save_favorites(path, fav)
    return True


def toggle_reaction(path: str, reaction_id: str) -> bool:
    fav = load_favorites(path)
    k = str(reaction_id)
    if k in fav.reactions:
        fav.reactions.remove(k)
        save_favorites(path, fav)
        return False
    fav.reactions.add(k)
    save_favorites(path, fav)
    return True
