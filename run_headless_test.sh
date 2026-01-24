#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [[ ! -x "$PROJECT_DIR/venv/bin/python" ]]; then
  echo "[ERROR] venv python not found: $PROJECT_DIR/venv/bin/python"
  exit 1
fi

# Запуск без графического интерфейса (для тестирования ИИ)
# Создаём временную директорию для модели
TEMP_DIR="$PROJECT_DIR/.temp_headless"
mkdir -p "$TEMP_DIR/models"

# Склеиваем модель если нужно
OFFLINE_MODEL_NAME="Llama-3.2-3B-Instruct-Q4_K_M.gguf"
OUT_PATH="$TEMP_DIR/models/$OFFLINE_MODEL_NAME"

if [[ ! -f "$OUT_PATH" || $(stat -f%z "$OUT_PATH" 2>/dev/null || stat -c%s "$OUT_PATH" 2>/dev/null) -eq 0 ]]; then
    echo "[INFO] Подготовка оффлайн модели..."
    ASSETS_DIR="$PROJECT_DIR/assets/models"
    parts=$(ls "$ASSETS_DIR"/${OFFLINE_MODEL_NAME}.part* | wc -l)
    echo "[INFO] Склейка $parts частей..."
    
    tmp_path="$OUT_PATH.tmp"
    cat "$ASSETS_DIR"/${OFFLINE_MODEL_NAME}.part* > "$tmp_path"
    mv "$tmp_path" "$OUT_PATH"
    
    size=$(du -h "$OUT_PATH" | cut -f1)
    echo "[INFO] Модель готова: $OUT_PATH ($size)"
fi

# Запускаем Python тест
echo "[INFO] Запуск теста ИИ..."
exec "$PROJECT_DIR/venv/bin/python" <<'EOF'
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from utils.ai_engine import AIEngine

PROJECT_DIR = Path.cwd()
HF_TOKEN_PATH = PROJECT_DIR / "data/secrets/hf_token.txt"
TEMP_DIR = PROJECT_DIR / ".temp_headless"
OFFLINE_MODEL_NAME = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
MODEL_PATH = TEMP_DIR / "models" / OFFLINE_MODEL_NAME

print("\n=== Инициализация ИИ движка ===")
engine = AIEngine(
    hf_token_path=str(HF_TOKEN_PATH),
    offline_model_path=str(MODEL_PATH)
)

time.sleep(3)

diag = engine.diagnose()
print(f"\nСтатус ИИ: {diag.mode}")
print(f"  HF токен: {'OK' if diag.hf_token_exists else 'Нет'}")
print(f"  Онлайн доступен: {'Да' if diag.online_reachable else 'Нет'}")
print(f"  Оффлайн модель: {'Да' if diag.offline_model_exists else 'Нет'}")
print(f"  llama_cpp: {'OK' if diag.llama_import_ok else 'Нет'}")

if diag.mode in ("ONLINE", "OFFLINE"):
    print(f"\n=== Тестовый запрос (режим: {diag.mode}) ===")
    questions = [
        "Что такое спирты в химии?",
        "Напиши уравнение реакции горения метана.",
        "Перечисли свойства карбоновых кислот.",
    ]
    
    for q in questions:
        print(f"\nВопрос: {q}")
        try:
            answer = engine.ask(q, timeout_sec=45)
            print(f"Ответ: {answer[:500]}..." if len(answer) > 500 else f"Ответ: {answer}")
        except Exception as e:
            print(f"Ошибка: {e}")
else:
    print(f"\nИИ недоступен")

engine.stop()
print("\n=== Тест завершен ===")
EOF
