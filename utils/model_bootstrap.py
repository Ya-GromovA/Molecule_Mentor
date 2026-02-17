from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Callable

from kivy.app import App


OFFLINE_MODEL_NAME = "Llama-3.2-1B-Instruct-Q4_K_M.gguf"
MODEL_DOWNLOAD_URL = "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf"
MODEL_SIZE_BYTES = 820_000_000
MODEL_MIN_BYTES = 200 * 1024 * 1024


def _project_root() -> Path:

    return Path(__file__).resolve().parent.parent


def _asset_models_dir() -> Path:
    return _project_root() / "assets" / "models"


def _is_complete_model(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        if path.stat().st_size < MODEL_MIN_BYTES:
            return False
        with path.open("rb") as f:
            return f.read(4) == b"GGUF"
    except OSError:
        return False


def _bundled_model_path() -> Optional[Path]:
    """Возвращает путь к модели, включённой в APK (FULL версия)."""
    models_dir = _asset_models_dir()

    candidates = [
        models_dir / "offline_model.gguf",
        models_dir / OFFLINE_MODEL_NAME,
    ]

    for p in candidates:
        if _is_complete_model(p):
            return p

    # Запасной вариант: если имя файла модели изменилось,
    # берем любой валидный GGUF из assets/models.
    for p in sorted(models_dir.glob("*.gguf")):
        if _is_complete_model(p):
            return p

    return None


def is_model_available(model_filename: str) -> bool:
    """Проверяет, доступна ли модель (уже собрана, есть части, или включена в APK)."""

    if _bundled_model_path() is not None:
        return True


    parts_dir = _asset_models_dir()
    parts = list(parts_dir.glob(f"{model_filename}.part*"))
    if len(parts) > 0:
        return True


    app = App.get_running_app()
    if app is None:
        return False

    user_dir = Path(app.user_data_dir).resolve()
    out_path = user_dir / "models" / model_filename

    if _is_complete_model(out_path):
        return True

    return False


def get_available_model_path(model_filename: str) -> Optional[Path]:
    """Возвращает путь к уже доступной модели без копирования."""
    bundled = _bundled_model_path()
    if bundled is not None:
        return bundled

    app = App.get_running_app()
    if app is None:
        return None

    user_dir = Path(app.user_data_dir).resolve()
    out_path = user_dir / "models" / model_filename
    if _is_complete_model(out_path):
        return out_path
    return None


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


    resume_pos = 0
    if tmp_path.exists():
        resume_pos = tmp_path.stat().st_size

    headers = {}
    if resume_pos > 0:
        headers["Range"] = f"bytes={resume_pos}-"

    response = requests.get(MODEL_DOWNLOAD_URL, headers=headers, stream=True, timeout=30)
    response.raise_for_status()


    if response.status_code == 206:
        content_range = response.headers.get("Content-Range", "")
        if "/" in content_range:
            total_size = int(content_range.split("/")[-1])
        else:
            total_size = MODEL_SIZE_BYTES
    else:
        total_size = int(response.headers.get("Content-Length", MODEL_SIZE_BYTES))
        resume_pos = 0

    mode = "ab" if resume_pos > 0 else "wb"
    downloaded = resume_pos

    with tmp_path.open(mode) as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total_size)

    if downloaded < MODEL_MIN_BYTES:
        raise RuntimeError(
            f"Скачивание завершилось преждевременно: {downloaded} из ~{MODEL_SIZE_BYTES} байт"
        )

    try:
        with tmp_path.open("rb") as f:
            if f.read(4) != b"GGUF":
                raise RuntimeError("Скачанный файл не является корректной GGUF моделью")
    except OSError as e:
        raise RuntimeError(f"Не удалось проверить скачанную модель: {e}")


    os.replace(tmp_path, out_path)
    return out_path


def ensure_gguf_ready(model_filename: str, parts_dir: Optional[Path] = None) -> Path:
    """
    Гарантирует, что итоговый .gguf существует в user_data_dir/models/.

    1. Если модель уже собрана в user_data_dir — возвращает путь
    2. Если модель включена в APK (FULL версия) — копирует её
    3. Если есть части (.part0000...) — собирает из них
    4. Если ничего нет — выбрасывает FileNotFoundError
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
    if out_path.exists():
        if _is_complete_model(out_path):
            return out_path
        try:
            out_path.unlink()
        except OSError:
            pass


    bundled = _bundled_model_path()
    if bundled is not None:
        # FULL версия: используем модель прямо из assets, не копируя ~500MB при старте.
        print(f"[MODEL] Используется встроенная модель из APK: {bundled}")
        return bundled

    if parts_dir is None:
        parts_dir = _asset_models_dir()

    parts = sorted(parts_dir.glob(f"{model_filename}.part*"))
    if not parts:
        raise FileNotFoundError(
            f"Model not found. Either download it first or include model parts in APK.\n"
            f"Expected: {out_path} or {parts_dir}/{model_filename}.part0000..."
        )

    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")


    with tmp_path.open("wb") as w:
        for part in parts:
            with part.open("rb") as r:
                while True:
                    buf = r.read(8 * 1024 * 1024)
                    if not buf:
                        break
                    w.write(buf)

    try:
        if tmp_path.stat().st_size < MODEL_MIN_BYTES:
            tmp_path.unlink(missing_ok=True)
            raise RuntimeError("Собранная модель повреждена или неполная")
    except OSError:
        pass

    os.replace(tmp_path, out_path)
    return out_path
