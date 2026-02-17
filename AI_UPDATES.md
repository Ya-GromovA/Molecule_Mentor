# ИИ-помощник в Molecule Mentor

Техническая документация по ИИ-движку приложения.

## Архитектура

### Дуальный режим работы

ИИ-движок (`utils/ai_engine.py`) поддерживает два режима:

| Режим | API | Модель | Требования |
|-------|-----|--------|------------|
| **ONLINE** | HuggingFace Inference API | Llama-3.1-8B-Instruct | Интернет + HF токен |
| **OFFLINE** | llama-cpp-python | Llama-3.2-3B-Q4_K_M | ~2 ГБ на диске |

### Автопереключение

 - Проверка соединения каждые 7 секунд
- При потере интернета — переход на офлайн
- При восстановлении — возврат на онлайн
 - Статус отображается в UI (ONLINE/OFFLINE/N/A). В интерфейсе обновление статуса может идти реже (например, раз в 15 секунд) — это нормально.

## Компоненты

### AIEngine (`utils/ai_engine.py`)

Основной класс ИИ-движка:

```python
class AIEngine:
    def __init__(self, hf_token_path: str, offline_model_path: str)
    def ask(self, question: str) -> str  # синхронный, вызывать из потока!
    def mode(self) -> str  # "ONLINE" | "OFFLINE" | "N/A"
    def diagnose(self) -> Diagnose  # диагностика состояния
    def stop() -> None  # остановка health-потока
```

**Важно:** метод `ask()` синхронный — вызывать только из фонового потока!

### Обработка ответов

1. **Промпты на русском** — строгое требование отвечать на русском языке
2. **Проверка качества** — `_is_answer_quality_good()` проверяет ответ
3. **Очистка текста** — удаление спецсимволов Unicode для совместимости с Kivy
4. **Повторные попытки** — до 3 попыток при некачественном ответе
5. **Фоллбэк** — "Я не знаю" если модель не справляется

### ModelDownloadScreen (`screens/model_download_screen.py`)

Экран загрузки модели для lite-версии:
- Скачивание частей модели с HuggingFace
- Прогресс-бар загрузки
- Автосклейка частей в единый .gguf файл

## Настройка

### Онлайн режим

1. Получите токен: https://huggingface.co/settings/tokens
2. Создайте файл `data/secrets/hf_token.txt`
3. Вставьте токен (начинается с `hf_...`)

```bash
mkdir -p data/secrets
echo "hf_ваш_токен" > data/secrets/hf_token.txt
```

### Офлайн режим

Модель загружается автоматически при первом запуске.

Расположение:
- **Desktop**: `data/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf`
- **Android (full)**: встроена в APK (`assets/models/`)
- **Android (lite)**: скачивается в app storage

## Тестирование

### Быстрый тест без UI

```bash
python -c "
from utils.ai_engine import AIEngine
ai = AIEngine('data/secrets/hf_token.txt', 'data/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf')
print(f'Mode: {ai.mode()}')
print(ai.diagnose())
ai.stop()
"
```

### Тест с вопросом

```bash
python test_ai_engine.py
```

### Проверка импортов

```bash
python -c "
from utils.ai_engine import AIEngine
from screens.ai_assistant_screen import AIAssistantScreen
print('OK')
"
```

## Диагностика

Метод `diagnose()` возвращает:

```python
@dataclass
class Diagnose:
    hf_token_exists: bool      # Есть ли HF токен
    hf_token_len: int          # Длина токена
    online_reachable: bool     # Доступен ли HF API
    online_last_error: str     # Последняя ошибка онлайн
    offline_model_exists: bool # Есть ли офлайн модель
    llama_import_ok: bool      # Импортируется ли llama_cpp
    llama_last_error: str      # Последняя ошибка llama
    mode: str                  # Текущий режим
    last_switch_ts: float      # Время последнего переключения
```

## Известные особенности

### Качество ответов

- Онлайн (8B) даёт более качественные ответы
- Офлайн (3B) может иногда допускать неточности
- Химические формулы сохраняются на латинице (H2O, NaCl)

### Производительность

- Первый запрос офлайн медленнее (загрузка модели в память)
- Последующие запросы быстрее
- На Android рекомендуется 4+ ГБ RAM

### Совместимость

- Kivy шрифты не поддерживают все Unicode символы
- Спецсимволы (стрелки, индексы) заменяются на простые
- Zero-width символы удаляются

## Структура файлов

```
utils/
├── ai_engine.py        # Основной ИИ-движок
└── model_bootstrap.py  # Подготовка/склейка модели

screens/
├── ai_assistant_screen.py   # UI чата с ИИ
└── model_download_screen.py # UI загрузки модели

data/
├── secrets/
│   └── hf_token.txt    # HuggingFace токен (не в git)
└── models/
    └── *.gguf          # Офлайн модель (не в git)
```
