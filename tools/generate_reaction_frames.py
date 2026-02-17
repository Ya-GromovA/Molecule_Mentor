


from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rdkit import Chem
from rdkit.Chem import AllChem


from utils.reaction_engine import REACTIONS, get_reaction


OUT_ROOT_DEFAULT = BASE_DIR / "assets" / "reactions"


def _safe_sanitize(m: Chem.Mol) -> Chem.Mol:
    try:
        m.UpdatePropertyCache(strict=False)
    except Exception:
        pass
    try:
        Chem.SanitizeMol(m)
    except Exception:
        try:
            m.UpdatePropertyCache(strict=False)
        except Exception:
            pass
    return m


def _contains_metal(m: Chem.Mol) -> bool:
    metals = {
        3, 4, 11, 12, 13, 19, 20,
        21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31,
        37, 38, 47, 48, 49, 56, 79
    }
    return any(a.GetAtomicNum() in metals for a in m.GetAtoms())


def _embed_3d(m: Chem.Mol, seed: int = 1) -> Chem.Mol:
    m = Chem.AddHs(m, addCoords=True)
    params = AllChem.ETKDGv3()
    if hasattr(params, "randomSeed"):
        params.randomSeed = int(seed)

    res = -1
    for _ in range(4):
        try:
            res = AllChem.EmbedMolecule(m, params)
        except Exception:
            res = -1
        if res == 0:
            break

    if res != 0:
        try:
            AllChem.EmbedMolecule(m, randomSeed=int(seed))
        except Exception:
            pass


    if not _contains_metal(m):
        try:
            AllChem.UFFOptimizeMolecule(m, maxIters=200)
        except Exception:
            pass

    return _safe_sanitize(m)


def _mol_from_smiles(smiles: str) -> Chem.Mol:
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    return _safe_sanitize(m)


def _combine(mols: List[Chem.Mol]) -> Chem.Mol:
    if not mols:
        return Chem.Mol()
    combo = mols[0]
    for m in mols[1:]:
        combo = Chem.CombineMols(combo, m)
    return combo


def _mol_to_atoms(m: Chem.Mol) -> List[Dict]:
    """
    Return 3D atoms with element and label.
    """
    conf = m.GetConformer()
    atoms: List[Dict] = []
    for i, a in enumerate(m.GetAtoms()):
        p = conf.GetAtomPosition(i)
        el = a.GetSymbol()
        atoms.append(
            {
                "element": el,
                "x": float(p.x),
                "y": float(p.y),
                "z": float(p.z),
                "label": f"{el}{i+1}",
            }
        )
    return atoms


def _center_atoms(atoms: List[Dict]) -> List[Dict]:
    if not atoms:
        return atoms
    xs = [a["x"] for a in atoms]
    ys = [a["y"] for a in atoms]
    zs = [a["z"] for a in atoms]
    cx = (min(xs) + max(xs)) / 2.0
    cy = (min(ys) + max(ys)) / 2.0
    cz = (min(zs) + max(zs)) / 2.0
    out = []
    for a in atoms:
        out.append(
            {
                **a,
                "x": a["x"] - cx,
                "y": a["y"] - cy,
                "z": a["z"] - cz,
            }
        )
    return out


def _spread_atoms(atoms: List[Dict], scale: float = 1.7) -> List[Dict]:

    out = []
    for a in atoms:
        out.append({**a, "x": a["x"] * scale, "y": a["y"] * scale, "z": a["z"] * scale})
    return out


def _stage_scene_normal(species: List[str], seed_base: int) -> Tuple[List[Dict], List[List[int]]]:
    mols = []
    for i, smi in enumerate(species):
        m = _mol_from_smiles(smi)
        m = _embed_3d(m, seed=seed_base + i * 17)
        mols.append(m)


    combo = _combine(mols)
    atoms = _center_atoms(_mol_to_atoms(combo))
    atoms = _spread_atoms(atoms, 1.7)


    bonds: List[List[int]] = []
    offset = 0
    for m in mols:
        for b in m.GetBonds():
            bonds.append([int(b.GetBeginAtomIdx()) + offset, int(b.GetEndAtomIdx()) + offset])
        offset += m.GetNumAtoms()

    return atoms, bonds


def _mapped_pool_atoms(pool_species: List[str], seed_base: int) -> Tuple[List[Dict], int]:
    """
    Build fixed atom pool and return atoms and count.
    """
    mols = []
    for i, smi in enumerate(pool_species):
        m = _mol_from_smiles(smi)
        m = _embed_3d(m, seed=seed_base + i * 31)
        mols.append(m)

    combo = _combine(mols)
    atoms = _center_atoms(_mol_to_atoms(combo))
    atoms = _spread_atoms(atoms, 1.9)
    return atoms, len(atoms)


def _diff_bonds(prev: List[Tuple[int, int]], cur: List[Tuple[int, int]]) -> Tuple[List[List[int]], List[List[int]]]:
    def norm(p: Tuple[int, int]) -> Tuple[int, int]:
        return (p[0], p[1]) if p[0] <= p[1] else (p[1], p[0])

    pset = {norm(x) for x in prev}
    cset = {norm(x) for x in cur}

    broken = sorted(pset - cset)
    formed = sorted(cset - pset)

    return ([list(x) for x in broken], [list(x) for x in formed])


def generate_for_reaction(reaction_id: str, out_root: Path, hold: int = 18) -> Path:
    rxn = get_reaction(reaction_id)
    if not rxn.stages:
        raise ValueError(f"Reaction '{reaction_id}' has no stages")

    out_dir = out_root / rxn.id
    out_dir.mkdir(parents=True, exist_ok=True)

    frames: List[Dict] = []
    stages_meta: List[Dict] = []



    mapped_pool_atoms: Optional[List[Dict]] = None
    mapped_pool_count: int = 0
    prev_bonds_override: List[Tuple[int, int]] = []

    cursor = 0
    for si, st in enumerate(rxn.stages):
        seed_base = abs(hash((rxn.id, si))) % 100000 + 1

        if getattr(st, "mapped", False):
            pool = list(getattr(st, "pool_species", []))
            if not pool:
                raise ValueError(f"{rxn.id} stage {si} is mapped=True but pool_species is empty")

            if mapped_pool_atoms is None:
                mapped_pool_atoms, mapped_pool_count = _mapped_pool_atoms(pool, seed_base=seed_base)

            bonds_override = list(getattr(st, "bonds_override", []))

            for a, b in bonds_override:
                if a < 0 or b < 0 or a >= mapped_pool_count or b >= mapped_pool_count:
                    raise ValueError(f"{rxn.id} stage {si} has bond ({a},{b}) out of range 0..{mapped_pool_count-1}")

            broken, formed = _diff_bonds(prev_bonds_override, bonds_override)

            start = cursor
            for _ in range(max(1, hold)):
                frames.append(
                    {
                        "atoms": mapped_pool_atoms,
                        "bonds": [list(x) for x in bonds_override],
                        "highlight_break": broken,
                        "highlight_form": formed,
                        "stage_index": si,
                    }
                )
                cursor += 1
            end = cursor - 1

            stages_meta.append(
                {
                    "title": st.title,
                    "description": st.description,
                    "note": getattr(st, "note", ""),
                    "happens": getattr(st, "happens", ""),
                    "mode": getattr(st, "mode", "none"),
                    "temperature_c": getattr(st, "temperature_c", None),
                    "frame_start": start,
                    "frame_end": end,
                    "mapped": True,
                }
            )
            prev_bonds_override = bonds_override
        else:
            atoms, bonds = _stage_scene_normal(getattr(st, "species", []), seed_base=seed_base)
            start = cursor
            for _ in range(max(1, hold)):
                frames.append(
                    {
                        "atoms": atoms,
                        "bonds": bonds,
                        "highlight_break": [],
                        "highlight_form": [],
                        "stage_index": si,
                    }
                )
                cursor += 1
            end = cursor - 1
            stages_meta.append(
                {
                    "title": st.title,
                    "description": st.description,
                    "note": getattr(st, "note", ""),
                    "happens": getattr(st, "happens", ""),
                    "mode": getattr(st, "mode", "none"),
                    "temperature_c": getattr(st, "temperature_c", None),
                    "frame_start": start,
                    "frame_end": end,
                    "mapped": False,
                }
            )

    payload = {
        "schema_version": 3,
        "reaction_id": rxn.id,
        "name": rxn.name,
        "equation": rxn.equation,
        "category": rxn.category,
        "steps": [asdict(s) for s in rxn.steps],
        "fps": 12,
        "frames": frames,
        "stages": stages_meta,
    }

    out_path = out_dir / "frames.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate offline frames.json for reactions.")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--id", type=str, default="")
    ap.add_argument("--out", type=str, default=str(OUT_ROOT_DEFAULT))
    ap.add_argument("--hold", type=int, default=18)
    args = ap.parse_args()

    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    if args.id:
        p = generate_for_reaction(args.id.strip(), out_root, hold=args.hold)
        print(f"[OK] {args.id}: -> {p}")
        return

    if args.all:
        ok = 0
        total = 0
        for r in REACTIONS:
            total += 1
            try:
                p = generate_for_reaction(r.id, out_root, hold=args.hold)
                print(f"[OK] {r.id}: -> {p}")
                ok += 1
            except Exception as e:
                print(f"[FAIL] {r.id}: {e}")
        print(f"Done. Generated: {ok}/{total}")
        return

    raise SystemExit("Use --all or --id <reaction_id>")


if __name__ == "__main__":
    main()
