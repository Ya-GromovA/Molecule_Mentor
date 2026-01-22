# Molecule Mentor 🧪

Интерактивное образовательное приложение для изучения химии с визуализацией молекул, курсами и ИИ-помощником.

## Возможности

- 📚 **Курсы по химии** - структурированные учебные материалы с разделами и темами
- 🧬 **Визуализация молекул** - 3D просмотр молекулярных структур
- ⚗️ **Химические реакции** - визуализация и описание реакций
- 📝 **Тесты и викторины** - проверка знаний с автоматическим подсчётом результатов
- 🤖 **ИИ-помощник** - помощь в изучении химии (онлайн и оффлайн режимы)
- 🎨 **Современный интерфейс** - Material Design 3 с адаптивной темой

## Технологии

- **Kivy** - кроссплатформенный UI фреймворк
- **KivyMD** - Material Design компоненты для Kivy
- **RDKit** - химическая информатика и вычислительная химия
- **py3Dmol** - визуализация молекул
- **llama-cpp-python** - локальный запуск языковых моделей

## Установка

### Требования

- Python 3.12+
- pip

### Шаги

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd molecule-mentor
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Подготовьте данные:
```bash
# Скопируйте hf_token.txt в data/secrets/ (для онлайн режима ИИ)
# Модель будет загружена автоматически при первом запуске
```

## Запуск

### Desktop (Linux/macOS/Windows)
```bash
python main.py
```

### Android
Для сборки Android приложения требуется [Buildozer](https://buildozer.readthedocs.io/):

```bash
pip install buildozer
buildozer android debug
```

## Структура проекта

```
molecule-mentor/
├── main.py                 # Точка входа приложения
├── requirements.txt        # Зависимости Python
├── buildozer.spec         # Конфигурация для Buildozer
├── theme.py               # Цветовая тема
├── screens/               # Экраны приложения
│   ├── home_screen.py
│   ├── courses_screen.py
│   ├── molecules_screen.py
│   └── ...
├── utils/                 # Утилиты и вспомогательные модули
│   ├── ai_engine.py       # ИИ-движок
│   ├── course_repo.py     # Работа с курсами
│   ├── molecule_db.py     # База молекул
│   └── ...
├── kv/                    # Kivy Language файлы
├── assets/                # Ресурсы (модели, изображения)
└── data/                  # Данные приложения
    ├── courses/           # База курсов
    ├── models/            # ИИ модели
    └── secrets/           # Секреты (токены)
```

## Лицензия

MIT License

## Контакты

Для вопросов и предложений создайте issue в репозитории.
