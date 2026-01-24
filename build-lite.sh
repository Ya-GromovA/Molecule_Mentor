#!/bin/bash
# Скрипт для сборки LITE версии APK (без AI-модели)
# Использование: ./build-lite.sh

set -e

cd "$(dirname "$0")"

echo "=== Сборка LITE версии (без AI-модели) ==="
echo ""

# Проверяем наличие файлов
if [ ! -f "buildozer-lite.spec" ]; then
    echo "ОШИБКА: buildozer-lite.spec не найден!"
    exit 1
fi

# Сохраняем оригинальный buildozer.spec если есть
if [ -f "buildozer.spec" ] && [ ! -L "buildozer.spec" ]; then
    echo "[1/5] Сохраняем оригинальный buildozer.spec -> buildozer-full.spec"
    mv buildozer.spec buildozer-full.spec
fi

# Создаём симлинк на lite версию
echo "[2/5] Переключаемся на buildozer-lite.spec"
rm -f buildozer.spec
ln -s buildozer-lite.spec buildozer.spec

# Запускаем сборку
echo "[3/5] Запускаем buildozer..."
echo ""
buildozer -v android debug

# Восстанавливаем оригинальный spec
echo ""
echo "[4/5] Восстанавливаем buildozer-full.spec"
rm -f buildozer.spec
if [ -f "buildozer-full.spec" ]; then
    mv buildozer-full.spec buildozer.spec
fi

# Переименовываем APK
echo "[5/5] Переименовываем APK..."
if [ -f "bin/moleculementor-0.1.0-arm64-v8a-debug.apk" ]; then
    mv bin/moleculementor-0.1.0-arm64-v8a-debug.apk bin/moleculementor-0.1.0-lite-arm64-v8a-debug.apk
    
    # Показываем размер
    SIZE=$(ls -lh bin/moleculementor-0.1.0-lite-arm64-v8a-debug.apk | awk '{print $5}')
    echo ""
    echo "=== ГОТОВО ==="
    echo "Файл: bin/moleculementor-0.1.0-lite-arm64-v8a-debug.apk"
    echo "Размер: $SIZE"
else
    echo "ПРЕДУПРЕЖДЕНИЕ: APK файл не найден в bin/"
fi
