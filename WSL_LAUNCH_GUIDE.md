# Запуск Molecule Mentor на WSL

Актуальная инструкция для WSL2 (Windows 10/11).

## 1) Требования

- Windows с WSL2
- Python 3.12+
- Созданный `venv` в корне проекта
- X-сервер (WSLg или VcXsrv)

## 2) Быстрый запуск

```bash
cd ~/molecule-mentor
./run_desktop_wsl.sh
```

Скрипт сам выставляет безопасные значения для WSL:
- `SDL_VIDEODRIVER=x11`
- `SDL_VIDEO_X11_FORCE_EGL=1`
- software OpenGL (`llvmpipe`) для стабильности

## 3) Проверка X11

```bash
echo $DISPLAY
timeout 3 xset q
```

- Если `xset q` не проходит, сначала поднимите X-сервер на Windows.
- Для WSLg обычно достаточно `DISPLAY=:0`.

## 4) Headless-проверка ИИ (без GUI)

```bash
cd ~/molecule-mentor
./run_headless_test.sh
```

Что делает скрипт:
- создает временную директорию `.temp_headless/`;
- при необходимости склеивает части GGUF-модели в `.temp_headless/models/`;
- запускает проверку `AIEngine` и тестовые запросы.

## 5) Частые проблемы

### Не стартует графика

```bash
export DISPLAY=:0
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe
./run_desktop_wsl.sh
```

### Не найден Python из `venv`

```bash
ls venv/bin/python
venv/bin/pip install -r requirements.txt
```

### Не работает online AI

```bash
ls -l data/secrets/hf_token.txt
```

Файл токена должен существовать локально и не попадать в git.

### Не работает offline AI

Проверьте наличие модели (или ее частей) в `assets/models/` и библиотек в `assets/llama/`.

## 6) Если WSL нестабилен

Соберите Android APK и тестируйте на устройстве:

```bash
./build-lite.sh
```
