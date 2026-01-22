from __future__ import annotations

import json
import os

from .chem_types import Atom, Reaction, ReactionFrame, ReactionMeta


class ReactionRepo:
    def __init__(self, reactions_root: str):
        self.reactions_root = reactions_root

    def list_reactions(self) -> list[dict]:
        if not os.path.isdir(self.reactions_root):
            return []
        items = []
        for name in sorted(os.listdir(self.reactions_root)):
            p = os.path.join(self.reactions_root, name)
            if not os.path.isdir(p):
                continue
            meta_path = os.path.join(p, "frames.json")
            if not os.path.exists(meta_path):
                continue
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                items.append({
                    "reaction_id": data.get("reaction_id", name),
                    "name": data.get("name", name),
                    "equation": data.get("equation", ""),
                    "category": data.get("category", ""),
                    "path": meta_path,
                })
            except Exception:
                continue
        return items

    def load_reaction(self, reaction_id: str) -> Reaction:
        meta_path = os.path.join(self.reactions_root, reaction_id, "frames.json")
        if not os.path.exists(meta_path):
            raise FileNotFoundError(meta_path)

        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = ReactionMeta(
            reaction_id=data.get("reaction_id", reaction_id),
            name=data.get("name", reaction_id),
            equation=data.get("equation", ""),
            category=data.get("category", ""),
            fps=int(data.get("fps", 12) or 12),
        )
        steps = data.get("steps", []) or []
        frames_raw = data.get("frames", []) or []
        frames: list[ReactionFrame] = []
        for fr in frames_raw:
            atoms = [
                Atom(
                    element=a.get("element", "C"),
                    x=float(a.get("x", 0.0)),
                    y=float(a.get("y", 0.0)),
                    z=float(a.get("z", 0.0)),
                    label=str(a.get("label", "")),
                )
                for a in (fr.get("atoms", []) or [])
            ]
            bonds = [tuple(b) for b in (fr.get("bonds", []) or [])]
            hb = [tuple(b) for b in (fr.get("highlight_break", []) or [])]
            hf = [tuple(b) for b in (fr.get("highlight_form", []) or [])]
            frames.append(
                ReactionFrame(
                    atoms=atoms,
                    bonds=[(int(i), int(j)) for i, j in bonds],
                    highlight_break=[(int(i), int(j)) for i, j in hb],
                    highlight_form=[(int(i), int(j)) for i, j in hf],
                    stage_index=int(fr.get("stage_index", 0) or 0),
                )
            )

        return Reaction(meta=meta, steps=steps, frames=frames)
