#!/bin/bash

# Оптимизация изображений для Android сборки
echo "Оптимизация изображений для Android..."

# Оптимизация иконок приложений
if command -v convert >/dev/null 2>&1; then
    echo "Оптимизация app_icon.png..."
    convert assets/icons/app_icon.png -resize 512x512 -quality 90 assets/icons/app_icon_optimized.png
    
    echo "Оптимизация presplash.png..."
    convert assets/icons/presplash.png -resize 1080x1920 -quality 85 assets/icons/presplash_optimized.png
    
    echo "Оптимизация splash.png..."
    convert assets/splash/splash.png -resize 1080x1920 -quality 85 assets/splash/splash_optimized.png
    
    echo "Замена оригиналов оптимизированными версиями..."
    mv assets/icons/app_icon_optimized.png assets/icons/app_icon.png
    mv assets/icons/presplash_optimized.png assets/icons/presplash.png
    mv assets/splash/splash_optimized.png assets/splash/splash.png
    
    echo "Оптимизация изображений завершена!"
else
    echo "ImageMagick не найден. Установите для оптимизации изображений."
    echo "sudo apt-get install imagemagick"
fi