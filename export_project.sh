#!/usr/bin/env bash
# ^^^^^^^^^^^^^^^^^^^^^^^^ КРИТИЧЕСКИ ВАЖНО: используем env для переносимости

OUTPUT_FILE="full_project_dump.txt"

# Очищаем файл перед записью
> "$OUTPUT_FILE"

# 1. Записываем структуру проекта
echo "🔥 PROJECT STRUCTURE" >> "$OUTPUT_FILE"
echo "==========================" >> "$OUTPUT_FILE"
if command -v tree &> /dev/null; then
    tree -a -I '__pycache__|.git|.venv|.mypy_cache|build|dist|*.egg-info|*.pyc|*.log|.vscode|.idea|*.swp|*.swo|*.DS_Store' \
        --charset utf-8 \
        --dirsfirst \
        -L 4 >> "$OUTPUT_FILE" 2>&1
else
    echo "[tree command not found - install with: sudo apt install tree]" >> "$OUTPUT_FILE"
    find . -type d ! -path "*/.*" | sed -e "s/[^-][^\/]*\//  |/g" -e "s/|\([^ ]\)/|-\1/" >> "$OUTPUT_FILE"
fi

# 2. Добавляем разделитель
echo -e "\n\n" >> "$OUTPUT_FILE"
echo "💻 FILE CONTENTS" >> "$OUTPUT_FILE"
echo "==========================" >> "$OUTPUT_FILE"
echo -e "\n" >> "$OUTPUT_FILE"

# 3. Рекурсивно обходим все файлы кода
find . -type f \( \
    -name "*.py" -o \
    -name "*.kv" -o \
    -name "*.md" -o \
    -name "*.txt" -o \
    -name "*.json" -o \
    -name "*.yaml" -o \
    -name "*.yml" -o \
    -name "*.sh" -o \
    -name "*.toml" -o \
    -name "*.ini" \
    \) \
    ! -path "*/.git/*" \
    ! -path "*/.venv/*" \
    ! -path "*/__pycache__/*" \
    ! -path "./venv/*" \
    ! -path "./.mypy_cache/*" \
    ! -path "./build/*" \
    ! -path "./dist/*" \
    | while read -r file; do
    echo "========== $file ==========" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    if [[ -f "$file" && ! -L "$file" ]]; then
        # Проверяем, является ли файл текстовым
        if file --mime-encoding "$file" | grep -q 'utf-8\|us-ascii\|iso-8859-1'; then
            cat "$file" >> "$OUTPUT_FILE" 2>/dev/null || echo "[ERROR READING FILE]" >> "$OUTPUT_FILE"
        else
            echo "[BINARY/ENCODED FILE - CONTENT SKIPPED]" >> "$OUTPUT_FILE"
        fi
    else
        echo "[FILE NOT FOUND OR IS A SYMLINK]" >> "$OUTPUT_FILE"
    fi
    echo -e "\n\n" >> "$OUTPUT_FILE"
done

echo "✅ Full project dump created: $(pwd)/$OUTPUT_FILE"
echo "👉 To open in Windows Explorer: explorer.exe \"$OUTPUT_FILE\""
