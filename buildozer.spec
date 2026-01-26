[app]
title = Molecule Mentor
package.name = moleculementor
package.domain = org.moleculementor
version = 0.1.0

source.dir = .
; LITE версия: БЕЗ частей модели (.part*) — модель скачивается при первом запуске
source.include_exts = py,kv,png,jpg,jpeg,json,pdb,txt,md,ttf,otf,so,bin,db

source.include_patterns = assets/**,kv/**,screens/**,utils/**,data/**,third_party/**,theme.py,main.py
; LITE версия: исключаем модели
source.exclude_patterns = **/*.bak,**/*.tmp,bin/**,.buildozer/**,venv/**,__pycache__/**,.git/**
source.exclude_dirs = assets/models

icon.filename = assets/icons/app_icon.png
presplash.filename = assets/icons/presplash.png
android.presplash_color = #000000

; Адаптивная иконка для Android 8+ (API 26+)
icon.adaptive_foreground.filename = assets/icons/app_icon.png
icon.adaptive_background.filename = assets/icons/app_icon.png

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,WAKE_LOCK

; Кастомный манифест с отключенным hardware acceleration (исправляет краш HWUI mutex)
android.manifest = android_manifest.xml

requirements = python3,kivy,numpy,pillow,requests,urllib3,pygments,docutils,pycparser,materialyoucolor,asynckivy,asyncgui,typing_extensions,https://github.com/kivymd/KivyMD/archive/master.zip

orientation = portrait
fullscreen = 0
log_level = 2

android.api = 34
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a
android.release_artifact = apk
android.skip_update = False

; Принудительно используем SDL2 bootstrap
p4a.bootstrap = sdl2

p4a.branch = master


[buildozer]
; Lite версия — модель скачивается при первом запуске
; Сборка: buildozer -v android debug -c buildozer-lite.spec
