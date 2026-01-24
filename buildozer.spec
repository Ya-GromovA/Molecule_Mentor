[app]
title = Molecule Mentor
package.name = moleculementor
package.domain = org.moleculementor
version = 0.1.0

source.dir = .
; ВАЖНО: части модели имеют расширение part0000.., иначе они не попадут в APK
source.include_exts = py,kv,png,jpg,jpeg,json,pdb,txt,md,ttf,otf,so,bin,part0000,part0001,part0002,part0003,part0004,part0005,part0006,part0007,part0008,part0009

source.include_patterns = assets/**,kv/**,screens/**,utils/**,data/**,theme.py,main.py
source.exclude_patterns = **/*.bak,**/*.tmp,bin/**,.buildozer/**,venv/**,__pycache__/**,.git/**

icon.filename = assets/icons/app_icon.png
presplash.filename = assets/icons/presplash.png
android.presplash_color = #000000

; Адаптивная иконка для Android 8+ (API 26+)
; Используем ту же иконку как foreground, фон будет цветом
icon.adaptive_foreground.filename = assets/icons/app_icon.png
icon.adaptive_background.filename = assets/icons/app_icon.png

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

requirements = python3,kivy,numpy,pillow,requests,urllib3,pygments,docutils,pycparser,https://github.com/kivymd/KivyMD/archive/master.zip

orientation = portrait
fullscreen = 0
log_level = 2

; ✅ ВОТ ЗДЕСЬ ДОЛЖНЫ БЫТЬ ВСЕ android.* настройки (в [app])
android.api = 34
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a
android.release_artifact = apk
android.skip_update = False

; Hardware acceleration is now enabled by default - removed problematic setting
; To disable for specific activity, would need to modify the bootstrap template

; Принудительно используем SDL2 bootstrap
p4a.bootstrap = sdl2

p4a.branch = master


[buildozer]
; можно оставить пустым или добавлять только buildozer.* параметры
