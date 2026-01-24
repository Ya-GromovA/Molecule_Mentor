# Запуск Molecule Mentor на WSL

Руководство по запуску приложения в Windows Subsystem for Linux.

## Требования

- Windows 10/11 с WSL2
- Python 3.12+
- X сервер для графики

## Установка X сервера

### Windows 11 22H2+ (WSLg)

WSLg встроен — проверьте:

```bash
echo $DISPLAY
# Должно вывести :0 или подобное
```

### Windows 10 / старые версии (VcXsrv)

1. Скачайте [VcXsrv](https://sourceforge.net/projects/vcxsrv/)
2. Запустите XLaunch:
   - Multiple windows
   - Display number: 0
   - Start no client
   - **Disable access control** (важно!)
3. Добавьте в `~/.bashrc`:

```bash
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
```

## Запуск

### С графикой

```bash
cd ~/molecule-mentor
./run_desktop_wsl.sh
```

### Без графики (тест ИИ)

```bash
./run_headless_test.sh
```

## Решение проблем

### GLX ошибки

```bash
# Программный рендеринг
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe
./run_desktop_wsl.sh
```

Альтернативы:
```bash
# Indirect GLX
export LIBGL_ALWAYS_INDIRECT=1

# EGL вместо GLX
export SDL_VIDEO_X11_FORCE_EGL=1
```

### Приложение не запускается

Проверьте:
```bash
which python3                    # Python установлен?
ls venv/bin/python               # venv создан?
venv/bin/pip list | head         # зависимости?
ls main.py kv/main.kv            # файлы на месте?
```

### ИИ не работает

```bash
# Проверка токена
cat data/secrets/hf_token.txt

# Проверка модели
ls -lh data/models/*.gguf

# Проверка llama_cpp
venv/bin/python -c "import llama_cpp; print('OK')"
```

## Альтернатива: Android

Для избежания проблем с X11 — соберите APK:

```bash
./build-lite.sh
# APK в bin/
```
