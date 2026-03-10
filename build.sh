#!/bin/bash

set -euo pipefail

MODE="${1:-all}"

if [ -x "./venv/bin/buildozer" ]; then
    BUILDOZER_BIN="./venv/bin/buildozer"
elif command -v buildozer >/dev/null 2>&1; then
    BUILDOZER_BIN="buildozer"
else
    echo "Ошибка: buildozer не найден. Установите его или создайте ./venv/bin/buildozer"
    exit 1
fi

build_variant() {
    local variant="$1"
    local spec_file="$2"
    local suffix="$3"

    echo "=== Сборка ${variant} (${spec_file}) ==="
    BUILDOZER_SPEC_FILE="${spec_file}" "${BUILDOZER_BIN}" -v android debug

    local base_apk
    base_apk=$(ls -t bin/moleculementor-*-arm64-v8a-debug.apk | grep -v -- "-lite-" | grep -v -- "-full-" | grep -v -- "-online-only-" | head -n 1)

    local final_apk="bin/moleculementor-$(grep '^version = ' "${spec_file}" | awk '{print $3}')-${suffix}-arm64-v8a-debug.apk"
    cp -f "${base_apk}" "${final_apk}"
    echo "=== Готово: ${final_apk} ==="
}

case "${MODE}" in
    full)
        build_variant "FULL" "buildozer-full.spec" "full"
        ;;
    lite)
        build_variant "LITE" "buildozer-lite.spec" "lite"
        ;;
    online-only|online)
        build_variant "ONLINE-ONLY" "buildozer-online.spec" "online-only"
        ;;
    all)
        build_variant "FULL" "buildozer-full.spec" "full"
        build_variant "LITE" "buildozer-lite.spec" "lite"
        build_variant "ONLINE-ONLY" "buildozer-online.spec" "online-only"
        ;;
    *)
        echo "Использование:"
        echo "  ./build.sh full"
        echo "  ./build.sh lite"
        echo "  ./build.sh online-only"
        echo "  ./build.sh all"
        exit 1
        ;;
esac
