[app]
title = Molecule Mentor
package.name = moleculementor
package.domain = org.moleculementor
version = 0.1.0

source.dir = .
; ВАЖНО: части модели имеют расширение part0000.., иначе они не попадут в APK
source.include_exts = py,kv,png,jpg,jpeg,json,pdb,txt,md,ttf,otf,so,bin,part0000,part0001,part0002,part0003,part0004,part0005,part0006,part0007,part0008,part0009

source.include_patterns = assets/**,kv/**,screens/**,utils/**,data/courses/**,data/secrets/**,theme.py,main.py
source.exclude_patterns = data/models/*.gguf,**/*.bak,**/*.tmp,bin/**,.buildozer/**,venv/**,__pycache__/**,.git/**

icon.filename = assets/icons/app_icon.png
presplash.filename = assets/icons/presplash.png
android.presplash_color = #000000

android.permissions = INTERNET,ACCESS_NETWORK_STATE

requirements = python3,kivy,numpy,pillow,requests,urllib3,pygments,docutils,pycparser,https://github.com/kivymd/KivyMD/archive/d668d8b.zip

orientation = portrait
fullscreen = 1
log_level = 2

; ✅ ВОТ ЗДЕСЬ ДОЛЖНЫ БЫТЬ ВСЕ android.* настройки (в [app])
android.api = 34
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a
android.release_artifact = apk
android.skip_update = True

p4a.branch = master


[buildozer]
; можно оставить пустым или добавлять только buildozer.* параметры
