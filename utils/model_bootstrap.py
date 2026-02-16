from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Callable

from kivy.app import App

# URL для скачивания модели (HuggingFace)
OFFLINE_MODEL_NAME = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
MODEL_DOWNLOAD_URL = "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
MODEL_SIZE_BYTES = 2_019_377_408  # ~1.88 GB
MODEL_MIN_BYTES = MODEL_SIZE_BYTES - (10 * 1024 * 1024)  # допускаем небольшой разброс


def _project_root() -> Path:
    # utils/model_bootstrap.py -> utils -> project root
    return Path(__file__).resolve().parent.parent


def _asset_models_dir() -> Path:
    return _project_root() / "assets" / "models"


def _is_complete_model(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        return path.stat().st_size >= MODEL_MIN_BYTES
    except OSError:
        return False


def _bundled_model_path() -> Optional[Path]:
    """Возвращает путь к модели, включённой в APK (FULL версия)."""
    bundled = _asset_models_dir() / "offline_model.gguf"
    if bundled.exists() and bundled.stat().st_size >= MODEL_MIN_BYTES:
        return bundled
    return None


def is_model_available(model_filename: str) -> bool:
    """Проверяет, доступна ли модель (уже собрана, есть части, или включена в APK)."""
    # Проверяем модель, включённую в APK (FULL версия)
    if _bundled_model_path() is not None:
        return True
    
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
    
    if _is_complete_model(out_path):
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

    if downloaded < MODEL_MIN_BYTES:
        raise RuntimeError(
            f"Скачивание завершилось преждевременно: {downloaded} из ~{MODEL_SIZE_BYTES} байт"
        )
    
    # Переименовываем в финальный файл
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

    # Проверяем модель, включённую в APK (FULL версия)
    bundled = _bundled_model_path()
    if bundled is not None:
        print(f"[MODEL] Копирование модели из APK: {bundled} -> {out_path}")
        tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
        try:
            import shutil
            shutil.copy2(bundled, tmp_path)
            os.replace(tmp_path, out_path)
            print(f"[MODEL] Модель скопирована успешно: {out_path.stat().st_size} байт")
            return out_path
        except Exception as e:
            print(f"[MODEL] Ошибка копирования модели: {e}")
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass

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

    try:
        if tmp_path.stat().st_size < MODEL_MIN_BYTES:
            tmp_path.unlink(missing_ok=True)
            raise RuntimeError("Собранная модель повреждена или неполная")
    except OSError:
        pass

    os.replace(tmp_path, out_path)
    return out_path
