from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from kivy.app import App


def _project_root() -> Path:
    # utils/model_bootstrap.py -> utils -> project root
    return Path(__file__).resolve().parent.parent


def _asset_models_dir() -> Path:
    return _project_root() / "assets" / "models"


def ensure_gguf_ready(model_filename: str, parts_dir: Optional[Path] = None) -> Path:
    """
    Гарантирует, что итоговый .gguf существует в user_data_dir/models/.
    Если нет — собирает из частей *.part0000... лежащих в assets/models.

    Возвращает путь к итоговому .gguf.
    """
    app = App.get_running_app()
    user_dir = Path(app.user_data_dir).resolve()
    out_dir = user_dir / "models"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / model_filename
    if out_path.exists() and out_path.stat().st_size > 0:
        return out_path

    if parts_dir is None:
        parts_dir = _asset_models_dir()

    parts = sorted(parts_dir.glob(f"{model_filename}.part*"))
    if not parts:
        raise FileNotFoundError(
            f"Model parts not found in {parts_dir}. Expected {model_filename}.part0000..."
        )

    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")

    # Склейка большими блоками, чтобы было быстрее
    with tmp_path.open("wb") as w:
        for part in parts:
            with part.open("rb") as r:
                while True:
                    buf = r.read(8 * 1024 * 1024)
                    if not buf:
                        break
                    w.write(buf)

    os.replace(tmp_path, out_path)
    return out_path
