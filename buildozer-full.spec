[app]
title = Molecule Mentor
package.name = moleculementor
package.domain = org.moleculementor
version = 0.2.2

source.dir = .
; LITE версия: модель не включена в APK (скачивание после установки)
; Native библиотеки llama.cpp добавляются через android.add_libs_arm64_v8a
source.include_exts = py,kv,png,jpg,jpeg,json,pdb,txt,md,ttf,otf,bin,db

source.include_patterns = assets/icons/**,assets/splash/**,assets/molecules/**,assets/reactions/**,assets/llama/**,assets/variant/lite.flag,assets/bg.png,kv/**,screens/**,utils/**,data/**,third_party/llama_cpp/**,theme.py,main.py
; LITE версия: исключаем встроенные модели
source.exclude_patterns = **/*.bak,**/*.tmp,bin/**,.buildozer/**,venv/**,__pycache__/**,.git/**,data/models/**,assets/models/**,third_party/llama.cpp/**

icon.filename = assets/icons/app_icon.png
presplash.filename = assets/icons/presplash.png
android.presplash_color = #000000

; Адаптивная иконка для Android 8+ (API 26+)
icon.adaptive_foreground.filename = assets/icons/app_icon.png
icon.adaptive_background.filename = assets/icons/app_icon.png

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,WAKE_LOCK

; Кастомный манифест с отключенным hardware acceleration (исправляет краш HWUI mutex)
android.manifest = android_manifest.xml

; Нативные библиотеки llama.cpp для arm64-v8a
; Эти файлы будут скопированы в jniLibs/arm64-v8a/ внутри APK
; и доступны через System.loadLibrary() или dlopen()
android.add_libs_arm64_v8a = assets/llama/*.so

requirements = python3,kivy,numpy,pillow,requests,urllib3,pygments,docutils,pycparser,materialyoucolor,asynckivy,asyncgui,typing_extensions,diskcache,jinja2,markupsafe,https://github.com/kivymd/KivyMD/archive/master.zip

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
; LITE версия — без встроенной GGUF-модели
