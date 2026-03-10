# Molecule Mentor

Molecule Mentor — Android-приложение для изучения химии: курсы, тесты, 3D-молекулы, анимации реакций и ИИ-помощник (онлайн/оффлайн).

## Что есть в проекте

### Обучение
- Курсы по химии (темы, разделы, теория)
- Тесты по разделам и викторины по категориям
- Статистика и прогресс
- Адаптивный учебный маршрут по слабым местам
- Режим подготовки к ОГЭ/ЕГЭ

### Визуализация
- Библиотека молекул с интерактивным 3D-просмотром
- Редактор молекул
- Библиотека анимированных реакций
- Редактор реакций

### ИИ
- Онлайн-режим через HuggingFace API
- Оффлайн-режим на локальной GGUF-модели
- Автовыбор режима
- Фоновая загрузка оффлайн-модели с прогрессом на главном экране

## Варианты APK

Проект поддерживает 3 сборки:

- `lite` — легкая сборка, модель скачивается после установки
- `full` — полная сборка
- `online-only` — только онлайн-ИИ

Текущая версия в `buildozer-*.spec`: `0.2.1`.

Артефакты debug-сборки:
- `bin/moleculementor-0.2.1-lite-arm64-v8a-debug.apk`
- `bin/moleculementor-0.2.1-full-arm64-v8a-debug.apk`
- `bin/moleculementor-0.2.1-online-only-arm64-v8a-debug.apk`

## Быстрый старт

### Требования
- Python 3.12+
- `pip`
- Для Android-сборки: Linux/WSL, Java 17, Android SDK/NDK, buildozer

### Запуск на Desktop

```bash
git clone https://github.com/Ya-GromovA/Molecule_Mentor.git
cd Molecule_Mentor

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python main.py
```

### Сборка Android

Рекомендуемый способ — через `build.sh`:

```bash
./build.sh lite
./build.sh full
./build.sh online-only
```

Скрипт автоматически подхватывает `./venv/bin/buildozer` (если есть) и формирует APK с правильным суффиксом варианта.

## ИИ: настройка и поведение

### Онлайн
Создайте файл `data/secrets/hf_token.txt` с токеном HuggingFace.

### Оффлайн
- Модель: `Llama-3.2-1B-Instruct-Q4_0.gguf`
- В `lite`/`full` доступна кнопка на главном экране: запуск загрузки в фоне
- Во время загрузки можно переходить по экранам: прогресс и остаток отображаются при возврате на главную

## Структура проекта (основное)

```text
molecule-mentor/
├── main.py
├── theme.py
├── kv/main.kv
├── build.sh
├── buildozer-lite.spec
├── buildozer-full.spec
├── buildozer-online.spec
├── screens/
│   ├── courses_screen.py
│   ├── course_topic_screen.py
│   ├── quiz_screen.py
│   ├── molecules_screen.py
│   ├── molecule_viewer_screen.py
│   ├── reactions_screen.py
│   ├── ai_assistant_screen.py
│   ├── model_download_screen.py
│   ├── adaptive_route_screen.py
│   ├── exam_prep_screen.py
│   ├── virtual_labs_screen.py
│   └── marquee_label.py
├── utils/
│   ├── ai_engine.py
│   ├── model_bootstrap.py
│   ├── visualizer_3d.py
│   └── course_repo.py
├── data/
│   ├── courses/
│   ├── quiz_questions.py
│   └── secrets/
└── assets/
    ├── molecules/
    ├── reactions/
    ├── icons/
    └── llama/
```

## Технологии

- Kivy 2.3.1 + KivyMD
- SQLite
- NumPy, Pillow
- HuggingFace API
- llama.cpp / llama-cpp-python
- Buildozer + python-for-android

## Документация

- [SESSION_LOG.md](SESSION_LOG.md) — хронология работ, проблемы и решения
- [AI_UPDATES.md](AI_UPDATES.md) — изменения в ИИ-части
- [COURSES_GUIDE.md](COURSES_GUIDE.md) — структура курсов
- [WSL_LAUNCH_GUIDE.md](WSL_LAUNCH_GUIDE.md) — запуск и отладка в WSL

## Лицензия

MIT

## Автор

Громова Александра
