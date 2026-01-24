# Molecule Mentor - Запуск на WSL/Windows

## Требования

1. **Windows 10/11 с WSL2**
2. **Python 3.12+** (установлен в WSL)
3. **X сервер для отображения графики** (один из вариантов):
   - **WSLg** (встроенный в Windows 11 22H2+)
   - **VcXsrv** (XLaunch)
   - **X410** (платный, но удобный)
   - **Xming**

## Установка X сервера

### Вариант 1: WSLg (рекомендуется для Windows 11 22H2+)

WSLg уже встроен в современные версии Windows. Проверьте, работает ли он:

```bash
# В WSL:
echo $DISPLAY
# Если выводит что-то вроде :0, :1, :10 и т.д. - WSLg работает
```

### Вариант 2: VcXsrv (Windows 10 и старые версии)

1. Скачайте и установите [VcXsrv](https://sourceforge.net/projects/vcxsrv/)
2. Запустите XLaunch:
   - "Multiple windows"
   - Display number: 0
   - "Start no client"
   - Включите "Disable access control"
3. Добавьте в `~/.bashrc`:

```bash
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
```

## Запуск приложения

### После настройки X сервера:

```bash
cd /home/ulyashka_88/molecule-mentor
./run_desktop_wsl.sh
```

### Если возникают проблемы с GLX:

Попробуйте разные комбинации переменных окружения:

```bash
# Вариант 1: С эмуляцией OpenGL (работает везде)
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe
./run_desktop_wsl.sh

# Вариант 2: С indirect GLX
export LIBGL_ALWAYS_INDIRECT=1
./run_desktop_wsl.sh

# Вариант 3: С EGL вместо GLX
export SDL_VIDEO_X11_FORCE_EGL=1
./run_desktop_wsl.sh
```

## Тестирование ИИ без графики

Для тестирования ИИ без запуска GUI:

```bash
./run_headless_test.sh
```

Это позволит проверить работу ИИ-движка и моделей.

## Статус ИИ в приложении

Статус ИИ отображается в правом верхнем углу:
- **ONLINE** (зелёный) - работает онлайн модель
- **OFFLINE** (синий) - работает офлайн модель
- **ИИ недоступен** (серый) - проблемы с подключением или моделями

## FAB кнопка (ИИ-помощник)

Кнопка с иконкой робота в правом нижнем углу открывает экран ИИ-помощника. Введите вопрос и нажмите "Отправить" для получения ответа.

## Решение проблем

### Проблема: "BadValue (integer parameter out of range for operation)"

Это ошибка GLX. Решения:
1. Установите правильный X сервер (см. выше)
2. Установите переменную `LIBGL_ALWAYS_SOFTWARE=1`
3. Попробуйте использовать WSLg на Windows 11

### Проблема: Приложение не запускается

Проверьте:
1. Python установлен: `which python3`
2. Виртуальное окружение создано: `ls -la venv/bin/python`
3. Зависимости установлены: `venv/bin/pip list`
4. Файлы на месте: `ls main.py kv/main.kv`

### Проблема: ИИ не отвечает

Проверьте:
1. Интернет-соединение (для онлайн-режима)
2. HF токен существует: `cat data/secrets/hf_token.txt`
3. Офлайн модель собрана: `ls -lh ~/.local/share/molecule-mentor/models/`
4. llama_cpp установлен: `venv/bin/python -c "import llama_cpp"`

## Альтернатива: запуск на Android

Для запуска на Android используйте Buildozer:

```bash
# Скомпилировать APK
buildozer android debug

# Установить на устройство
buildozer android deploy run
```

Android-версия не требует X11 и работает нативно.
