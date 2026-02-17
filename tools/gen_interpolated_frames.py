
from __future__ import annotations

import argparse
import json
from pathlib import Path


def frame_sig(fr):
    atoms = fr.get("atoms", [])[:8]
    return tuple(
        (a.get("element"), round(a.get("x", 0.0), 3), round(a.get("y", 0.0), 3), round(a.get("z", 0.0), 3))
        for a in atoms
    )


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def ease_in_out(t: float) -> float:

    return t * t * (3.0 - 2.0 * t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frames_json", help="Path to assets/reactions/<id>/frames.json")
    ap.add_argument("--out_dir", required=True, help="Output reaction directory (will create/overwrite frames.json)")
    ap.add_argument("--frames", type=int, default=48, help="Number of output frames")
    ap.add_argument("--fps", type=int, default=12, help="FPS in meta")
    args = ap.parse_args()

    src = Path(args.frames_json)
    data = json.loads(src.read_text(encoding="utf-8"))

    frames = data.get("frames", [])
    if not frames:
        raise SystemExit("No frames in source")


    f0 = frames[0]
    sig0 = frame_sig(f0)

    f1 = None
    for fr in frames[1:]:
        if frame_sig(fr) != sig0:
            f1 = fr
            break
    if f1 is None:

        f1 = frames[-1]

    a0 = f0.get("atoms", [])
    a1 = f1.get("atoms", [])
    if len(a0) != len(a1):
        raise SystemExit(f"Atom count mismatch: {len(a0)} vs {len(a1)}")

    bonds = f0.get("bonds", [])
    out_frames = []

    n = max(2, int(args.frames))
    for i in range(n):
        t = i / (n - 1)
        tt = ease_in_out(t)

        atoms = []
        for p, q in zip(a0, a1):
            atoms.append(
                {
                    "element": p.get("element"),
                    "label": p.get("label"),
                    "x": lerp(float(p.get("x", 0.0)), float(q.get("x", 0.0)), tt),
                    "y": lerp(float(p.get("y", 0.0)), float(q.get("y", 0.0)), tt),
                    "z": lerp(float(p.get("z", 0.0)), float(q.get("z", 0.0)), tt),
                }
            )

        out_frames.append(
            {
                "stage_index": f0.get("stage_index", 0),
                "atoms": atoms,
                "bonds": bonds,
                "highlight_break": f0.get("highlight_break", []),
                "highlight_form": f0.get("highlight_form", []),
            }
        )

    out = dict(data)
    out["meta"] = dict(out.get("meta", {}))
    out["meta"]["fps"] = int(args.fps)
    out["frames"] = out_frames

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "frames.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Wrote:", out_dir / "frames.json")
    print("frames:", len(out_frames))


if __name__ == "__main__":
    main()
