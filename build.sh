#!/bin/bash
# Скрипт для сборки APK
# Использование:
#   ./build.sh full   - сборка с моделью (~2 ГБ)
#   ./build.sh lite   - сборка без модели (~50-100 МБ)

set -e

if [ "$1" == "lite" ]; then
    echo "=== Сборка LITE версии (без AI-модели) ==="
    BUILDOZER_SPEC_FILE=buildozer-lite.spec buildozer -v android debug
    
    # Переименовываем APK для ясности
    if [ -f bin/moleculementor-0.1.0-arm64-v8a-debug.apk ]; then
        mv bin/moleculementor-0.1.0-arm64-v8a-debug.apk bin/moleculementor-0.1.0-lite-arm64-v8a-debug.apk
        echo "=== Готово: bin/moleculementor-0.1.0-lite-arm64-v8a-debug.apk ==="
    fi
    
elif [ "$1" == "full" ]; then
    echo "=== Сборка FULL версии (с AI-моделью) ==="
    buildozer -v android debug
    echo "=== Готово: bin/moleculementor-0.1.0-arm64-v8a-debug.apk ==="
    
else
    echo "Использование:"
    echo "  ./build.sh full   - сборка с моделью (~2 ГБ)"
    echo "  ./build.sh lite   - сборка без модели (~50-100 МБ)"
    exit 1
fi
