#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# --- Display / X11 ---
# Можно переопределить: DISPLAY=:0 ./run_desktop_wsl.sh
export DISPLAY="${DISPLAY:-:0}"

# --- Kivy backend для WSL ---
# Пытаемся использовать EGL вместо GLX для лучшей совместимости с WSL
export KIVY_WINDOW="${KIVY_WINDOW:-sdl2}"

# Для WSL1/2 с Windows X server (VcXsrv, XLaunch)
export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-x11}"
export SDL_VIDEO_X11_FORCE_EGL="${SDL_VIDEO_X11_FORCE_EGL:-1}"

# --- OpenGL: software render (надёжно для WSL) ---
export LIBGL_ALWAYS_SOFTWARE="${LIBGL_ALWAYS_SOFTWARE:-1}"
export GALLIUM_DRIVER="${GALLIUM_DRIVER:-llvmpipe}"
export MESA_LOADER_DRIVER_OVERRIDE="${MESA_LOADER_DRIVER_OVERRIDE:-llvmpipe}"

# Задаём минимальную версию OpenGL (если драйвер не сообщает версию)
export MESA_GL_VERSION_OVERRIDE="${MESA_GL_VERSION_OVERRIDE:-3.3}"
export MESA_GLSL_VERSION_OVERRIDE="${MESA_GLSL_VERSION_OVERRIDE:-330}"

# Включаем indirect GLX если прямые вызовы не работают
# (часто нужно для X серверов на Windows)
export LIBGL_ALWAYS_INDIRECT="${LIBGL_ALWAYS_INDIRECT:-0}"

# --- Kivy logging ---
export KIVY_LOG_LEVEL="${KIVY_LOG_LEVEL:-info}"

# --- Sanity checks ---
if [[ ! -x "$PROJECT_DIR/venv/bin/python" ]]; then
  echo "[ERROR] venv python not found: $PROJECT_DIR/venv/bin/python"
  echo "Activate venv or recreate it. Expected venv at: $PROJECT_DIR/venv"
  exit 1
fi

if [[ ! -f "$PROJECT_DIR/main.py" ]]; then
  echo "[ERROR] main.py not found in: $PROJECT_DIR"
  exit 1
fi

echo "[INFO] Project: $PROJECT_DIR"
echo "[INFO] Python:  $PROJECT_DIR/venv/bin/python"
echo "[INFO] DISPLAY=${DISPLAY}"
echo "[INFO] SDL_VIDEODRIVER=${SDL_VIDEODRIVER} | FORCE_EGL=${SDL_VIDEO_X11_FORCE_EGL}"
echo "[INFO] Software GL: LIBGL_ALWAYS_SOFTWARE=${LIBGL_ALWAYS_SOFTWARE}, GALLIUM_DRIVER=${GALLIUM_DRIVER}"

# --- Проверка X11 соединения ---
echo "[INFO] Проверка X11 соединения..."
if ! timeout 3 xset q >/dev/null 2>&1; then
    echo "[WARNING] X11 сервер недоступен (DISPLAY=${DISPLAY})"
    echo "[WARNING] Убедитесь, что:"
    echo "  1) На Windows установлен X сервер (VcXsrv, XLaunch или WSLg)"
    echo "  2) X сервер запущен и разрешён вход с WSL (disable access control)"
    echo "  3) Переменная DISPLAY установлена корректно"
    echo ""
    echo "[INFO] Попытка запуска в любом случае..."
fi

# --- Run ---
exec "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/main.py"
