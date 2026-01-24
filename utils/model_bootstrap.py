from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Callable

from kivy.app import App

# URL для скачивания модели (HuggingFace)
MODEL_DOWNLOAD_URL = "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
MODEL_SIZE_BYTES = 2_019_377_408  # ~1.88 GB


def _project_root() -> Path:
    # utils/model_bootstrap.py -> utils -> project root
    return Path(__file__).resolve().parent.parent


def _asset_models_dir() -> Path:
    return _project_root() / "assets" / "models"


def is_model_available(model_filename: str) -> bool:
    """Проверяет, доступна ли модель (уже собрана или есть части для сборки)."""
    # Сначала проверяем части — они не зависят от App
    parts_dir = _asset_models_dir()
    parts = list(parts_dir.glob(f"{model_filename}.part*"))
    if len(parts) > 0:
        return True
    
    # Проверяем собранную модель в user_data_dir
    app = App.get_running_app()
    if app is None:
        return False
    
    user_dir = Path(app.user_data_dir).resolve()
    out_path = user_dir / "models" / model_filename
    
    if out_path.exists() and out_path.stat().st_size > 0:
        return True
    
    return False


def needs_download(model_filename: str) -> bool:
    """Проверяет, нужно ли скачивать модель (нет ни готовой модели, ни частей)."""
    return not is_model_available(model_filename)


def download_model(
    model_filename: str,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Path:
    """
    Скачивает модель с HuggingFace.
    
    Args:
        model_filename: Имя файла модели (например, "Llama-3.2-3B-Instruct-Q4_K_M.gguf")
        progress_callback: Функция обратного вызова (downloaded_bytes, total_bytes)
    
    Returns:
        Path к скачанному файлу
    
    Raises:
        Exception: При ошибке скачивания
    """
    import requests
    
    app = App.get_running_app()
    if app is None:
        raise RuntimeError("App not running")
    
    user_dir = Path(app.user_data_dir).resolve()
    out_dir = user_dir / "models"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    out_path = out_dir / model_filename
    tmp_path = out_path.with_suffix(out_path.suffix + ".download")
    
    # Проверяем, есть ли частично скачанный файл (для resume)
    resume_pos = 0
    if tmp_path.exists():
        resume_pos = tmp_path.stat().st_size
    
    headers = {}
    if resume_pos > 0:
        headers["Range"] = f"bytes={resume_pos}-"
    
    response = requests.get(MODEL_DOWNLOAD_URL, headers=headers, stream=True, timeout=30)
    response.raise_for_status()
    
    # Определяем общий размер
    if response.status_code == 206:  # Partial Content (resume)
        content_range = response.headers.get("Content-Range", "")
        if "/" in content_range:
            total_size = int(content_range.split("/")[-1])
        else:
            total_size = MODEL_SIZE_BYTES
    else:
        total_size = int(response.headers.get("Content-Length", MODEL_SIZE_BYTES))
        resume_pos = 0  # Сервер не поддержал resume, начинаем заново
    
    mode = "ab" if resume_pos > 0 else "wb"
    downloaded = resume_pos
    
    with tmp_path.open(mode) as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1 MB chunks
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total_size)
    
    # Переименовываем в финальный файл
    os.replace(tmp_path, out_path)
    return out_path


def ensure_gguf_ready(model_filename: str, parts_dir: Optional[Path] = None) -> Path:
    """
    Гарантирует, что итоговый .gguf существует в user_data_dir/models/.
    
    1. Если модель уже собрана — возвращает путь
    2. Если есть части (.part0000...) — собирает из них
    3. Если ничего нет — выбрасывает FileNotFoundError
       (для Lite версии нужно сначала вызвать download_model)

    Возвращает путь к итоговому .gguf.
    """
    app = App.get_running_app()
    if app is None:
        raise RuntimeError("App not running")
    
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
            f"Model not found. Either download it first or include model parts in APK.\n"
            f"Expected: {out_path} or {parts_dir}/{model_filename}.part0000..."
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
