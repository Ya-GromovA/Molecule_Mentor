
from __future__ import annotations

import argparse
from pathlib import Path


def split_file(src: Path, out_dir: Path, chunk_mb: int) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    chunk_size = chunk_mb * 1024 * 1024

    parts: list[Path] = []
    idx = 0
    with src.open("rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            part = out_dir / f"{src.name}.part{idx:04d}"
            part.write_bytes(data)
            parts.append(part)
            idx += 1
    return parts


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True, help="Path to .gguf")
    p.add_argument("--out", required=True, help="Output dir for parts")
    p.add_argument("--chunk-mb", type=int, default=200, help="Chunk size MB (default 200)")
    args = p.parse_args()

    src = Path(args.src).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()

    if not src.exists():
        raise SystemExit(f"Source file not found: {src}")

    parts = split_file(src, out_dir, args.chunk_mb)

    total = sum(x.stat().st_size for x in parts)
    print(f"Split OK: {len(parts)} parts -> {out_dir}")
    print(f"Total parts size: {total / (1024**3):.2f} GB")
    print("First/last part:", parts[0].name, parts[-1].name)


if __name__ == "__main__":
    main()
