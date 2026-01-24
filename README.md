# Molecule Mentor

Интерактивное образовательное Android-приложение для изучения химии с 3D визуализацией молекул, анимациями реакций, курсами и ИИ-помощником.

## Возможности

### Обучение
- **Курсы по химии** — структурированные учебные материалы с разделами и темами
- **Теоретический материал** — подробные объяснения с формулами и примерами
- **Тесты и викторины** — проверка знаний с автоматическим подсчётом результатов и отслеживанием прогресса

### Визуализация
- **3D просмотр молекул** — интерактивная визуализация 27 молекулярных структур (вода, метан, бензол, глюкоза и др.)
- **Редактор молекул** — создание и редактирование собственных молекул
- **Анимации реакций** — 20 химических реакций с пошаговой визуализацией (горение, нейтрализация, электролиз и др.)
- **Редактор реакций** — создание собственных анимаций реакций

### ИИ-помощник
- **Онлайн режим** — Llama-3.1-8B через HuggingFace API
- **Офлайн режим** — Llama-3.2-3B локально через llama.cpp
- **Автопереключение** — автоматический выбор режима в зависимости от интернета
- **Русский язык** — оптимизированные промпты для ответов на русском

### Интерфейс
- **Material Design 3** — современный адаптивный дизайн
- **Тёмная тема** — комфортная работа при любом освещении
- **Статус ИИ** — индикатор состояния (ONLINE/OFFLINE) в реальном времени

## Скриншоты

| Главный экран | Молекулы | 3D Просмотр |
|---------------|----------|-------------|
| Навигация по разделам | Библиотека молекул | Интерактивная визуализация |

## Технологии

| Компонент | Технология |
|-----------|------------|
| UI Framework | Kivy 2.3.1 + KivyMD |
| 3D визуализация | py3Dmol, OpenGL |
| Химия | RDKit |
| ИИ (онлайн) | HuggingFace Inference API |
| ИИ (офлайн) | llama-cpp-python |
| База данных | SQLite |
| Сборка Android | Buildozer (python-for-android) |

## Установка

### Требования

- Python 3.12+
- pip
- Для Android сборки: Linux/WSL, Java 17, Android SDK/NDK

### Запуск на Desktop

```bash
# Клонирование
git clone https://github.com/Ya-GromovA/Molecule_Mentor.git
cd Molecule_Mentor

# Виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/macOS
# или: venv\Scripts\activate  # Windows

# Зависимости
pip install -r requirements.txt

# Запуск
python main.py
```

### Сборка Android APK

**Lite версия** (~50 МБ, модель скачивается при первом запуске):
```bash
./build-lite.sh
# или: buildozer -v android debug -c buildozer-lite.spec
```

**Полная версия** (~2 ГБ, модель встроена):
```bash
./build.sh
# или: buildozer -v android debug
```

### Настройка ИИ

1. **Для онлайн режима**: создайте файл `data/secrets/hf_token.txt` с вашим [HuggingFace токеном](https://huggingface.co/settings/tokens)

2. **Для офлайн режима**: модель скачивается автоматически при первом запуске (~2 ГБ)

## Структура проекта

```
molecule-mentor/
├── main.py                     # Точка входа
├── theme.py                    # Цветовая тема Material Design
├── requirements.txt            # Python зависимости
├── buildozer.spec              # Конфиг полной версии
├── buildozer-lite.spec         # Конфиг lite версии
│
├── screens/                    # Экраны приложения (15 модулей)
│   ├── home_screen.py          # Главный экран
│   ├── courses_screen.py       # Список курсов
│   ├── course_topic_screen.py  # Темы курса
│   ├── theory_screen.py        # Теоретический материал
│   ├── quiz_screen.py          # Тесты
│   ├── molecules_screen.py     # Библиотека молекул
│   ├── molecule_viewer_screen.py   # 3D просмотр молекулы
│   ├── molecule_editor_screen.py   # Редактор молекул
│   ├── reactions_screen.py     # Библиотека реакций
│   ├── reaction_viewer_screen.py   # Анимация реакции
│   ├── reaction_editor_screen.py   # Редактор реакций
│   ├── ai_assistant_screen.py  # ИИ-помощник
│   └── model_download_screen.py    # Загрузка модели
│
├── utils/                      # Утилиты
│   ├── ai_engine.py            # ИИ движок (онлайн + офлайн)
│   ├── visualizer_3d.py        # 3D визуализация
│   ├── model_bootstrap.py      # Загрузка/сборка модели
│   ├── course_repo.py          # Репозиторий курсов
│   ├── reaction_repo.py        # Репозиторий реакций
│   ├── molecule_db.py          # База молекул
│   └── db.py                   # SQLite утилиты
│
├── kv/                         # Kivy Language разметка
│   └── main.kv
│
├── assets/                     # Ресурсы
│   ├── molecules/              # 27 PDB файлов молекул
│   ├── reactions/              # 20 анимаций реакций
│   ├── icons/                  # Иконки приложения
│   └── models/                 # Части модели для полной версии
│
├── data/                       # Данные
│   ├── courses/                # База курсов (SQLite)
│   ├── models/                 # ИИ модели (для разработки)
│   └── secrets/                # Токены (не в git)
│
└── tools/                      # Инструменты разработки
    ├── generate_molecules.py   # Генерация PDB файлов
    ├── generate_reaction_frames.py  # Генерация анимаций
    ├── generate_courses_content.py  # Генерация контента курсов
    └── seed_quizzes.py         # Заполнение тестов
```

## Библиотека молекул

27 молекул с 3D структурами:

| Категория | Молекулы |
|-----------|----------|
| Простые | H₂O, H₂, O₂, N₂, CO₂, NH₃, HCl |
| Углеводороды | CH₄, C₂H₆, C₃H₈, C₄H₁₀, C₆H₆, толуол |
| Спирты | CH₃OH, C₂H₅OH, глицерин, фенол |
| Кислоты | HCOOH, CH₃COOH, HNO₃, H₂SO₄ |
| Другие | NaCl, NaOH, ацетон, мочевина, глюкоза, глицин, аланин |

## Библиотека реакций

20 анимированных реакций:

- Горение метана
- Нейтрализация (HCl + NaOH)
- Электролиз воды
- Разложение H₂O₂
- Процесс Габера (синтез аммиака)
- Гидрирование этилена
- Дегидратация этанола
- Полимеризация этилена
- Эстерификация
- Омыление
- И другие...

## Документация

- [AI_UPDATES.md](AI_UPDATES.md) — описание ИИ-функционала
- [COURSES_GUIDE.md](COURSES_GUIDE.md) — руководство по курсам
- [WSL_LAUNCH_GUIDE.md](WSL_LAUNCH_GUIDE.md) — запуск в WSL

## Лицензия

MIT License

## Автор

Громова Александра

## Ссылки

- [Репозиторий](https://github.com/Ya-GromovA/Molecule_Mentor)
- [Kivy Documentation](https://kivy.org/doc/stable/)
- [KivyMD](https://kivymd.readthedocs.io/)
