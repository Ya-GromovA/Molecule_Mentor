# Курсы в Molecule Mentor

Актуальная схема курсов, тестов и прогресса в приложении.

## 1) Как устроен учебный контент

```
Курс
└── Раздел
    └── Тема
        └── Блок (текст/изображение)
```

- Курс: верхний уровень (например, химия 10 класса).
- Раздел: крупная тематическая часть курса.
- Тема: конкретный учебный материал внутри раздела.
- Блок: единица контента для показа на экране теории.

## 2) Навигация пользователя

1. Главный экран -> `Курсы`
2. Экран курсов -> выбор курса
3. Экран тем курса -> выбор темы
4. Экран теории -> чтение блоков
5. Экран тестов -> запуск теста по разделу или квиза по категории

## 3) Где хранятся данные

- Основная база: `data/courses/courses.db`
- Категорийные квизы: `data/quiz_questions.py` (bank вопросов/seed)

## 4) Актуальные таблицы SQLite

### Контент курсов

- `courses` — курсы (`id`, `grade`, `level`, `title`, ...)
- `course_sections` — разделы курса (`course_id`, `section_key`, `title`, `position`)
- `course_topics` — темы раздела (`section_id`, `topic_key`, `title`, `position`)
- `topic_blocks` — блоки теории (`topic_id`, `block_type`, `content`, `caption`, `position`)

### Тестирование и прогресс

- `mm_quizzes` — карточки тестов/квизов
- `mm_quiz_questions` — вопросы для конкретного квиза
- `mm_quiz_attempts` — история попыток (score/total/percent)
- `mm_course_progress` — агрегированный прогресс по курсу
- `mm_app_meta` — служебные метаданные (версия/состояние данных)

Примечание: в базе могут присутствовать legacy-таблицы (`sections`, `topics`, `quizzes`, `quiz_questions`) для совместимости и миграций.

## 5) Логика прогресса

- После завершения теста пишется попытка в `mm_quiz_attempts`.
- Прогресс курса обновляется в `mm_course_progress`:
  - `best_percent` — лучший результат,
  - `last_percent` — последний результат,
  - `attempts_count` — число попыток,
  - `updated_at` — время последнего обновления.

## 6) Полезные команды

```bash
# Проверка целостности и содержимого БД
python tools/check_courses_db.py

# Заполнение/обновление квизов
python tools/seed_quizzes.py

# Миграции структуры курсов
python tools/migrate_courses_sections.py
python tools/migrate_quizzes_and_progress.py

# Генерация/обновление контента курсов
python tools/generate_courses_content.py
```
