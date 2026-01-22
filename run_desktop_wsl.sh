#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# --- Display / X11 ---
# Можно переопределить: DISPLAY=:0 ./run_desktop_wsl.sh
export DISPLAY="${DISPLAY:-:0}"

# --- SDL / Kivy window backend ---
export KIVY_WINDOW="${KIVY_WINDOW:-sdl2}"
export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-x11}"

# Важно: уходим с GLX (который в WSL часто падает) на EGL
export SDL_VIDEO_X11_FORCE_EGL="${SDL_VIDEO_X11_FORCE_EGL:-1}"

# --- OpenGL: software render (стабильно для WSL) ---
export LIBGL_ALWAYS_SOFTWARE="${LIBGL_ALWAYS_SOFTWARE:-1}"
export GALLIUM_DRIVER="${GALLIUM_DRIVER:-llvmpipe}"
export MESA_LOADER_DRIVER_OVERRIDE="${MESA_LOADER_DRIVER_OVERRIDE:-llvmpipe}"

# Часто стабилизирует контекст/шейдеры в софт-рендере
export MESA_GL_VERSION_OVERRIDE="${MESA_GL_VERSION_OVERRIDE:-3.3}"
export MESA_GLSL_VERSION_OVERRIDE="${MESA_GLSL_VERSION_OVERRIDE:-330}"

# Иногда помогает, если система упорно пытается в indirect GLX
# (оставляем выключенным по умолчанию — включай при необходимости)
# export LIBGL_ALWAYS_INDIRECT=1

# --- Kivy logging (чтобы логи были читаемыми) ---
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

# --- Run ---
exec "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/main.py"
