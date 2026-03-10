[app]
title = Molecule Mentor
package.name = moleculementor
package.domain = org.moleculementor
version = 0.2.1

source.dir = .
; ONLINE-ONLY версия: только онлайн ИИ, без оффлайн-модели и без экрана скачивания
source.include_exts = py,kv,png,jpg,jpeg,json,pdb,txt,md,ttf,otf,bin,db

source.include_patterns = assets/icons/**,assets/splash/**,assets/molecules/**,assets/reactions/**,assets/llama/**,assets/variant/online_only.flag,assets/bg.png,kv/**,screens/**,utils/**,data/**,third_party/llama_cpp/**,theme.py,main.py
source.exclude_patterns = **/*.bak,**/*.tmp,bin/**,.buildozer/**,venv/**,__pycache__/**,.git/**,data/models/**,assets/models/**,third_party/llama.cpp/**

icon.filename = assets/icons/app_icon.png
presplash.filename = assets/icons/presplash.png
android.presplash_color = #000000

icon.adaptive_foreground.filename = assets/icons/app_icon.png
icon.adaptive_background.filename = assets/icons/app_icon.png

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,WAKE_LOCK
android.manifest = android_manifest.xml
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

p4a.bootstrap = sdl2
p4a.branch = master

[buildozer]
; ONLINE-ONLY версия — только онлайн ИИ, без загрузки оффлайн-модели
