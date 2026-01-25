from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

RGBA = Tuple[float, float, float, float]


@dataclass(frozen=True)
class AppTheme:
    # набор цветов для приложения
    bg: RGBA
    surface: RGBA
    surface2: RGBA
    primary: RGBA
    accent: RGBA
    button_color: RGBA
    text: RGBA
    text2: RGBA


THEME = AppTheme(
    bg=(0.12, 0.15, 0.25, 1.0),        # основной фон
    surface=(0.10, 0.12, 0.18, 1.0),   # фон карточек
    surface2=(0.13, 0.16, 0.24, 1.0),  # чуть светлее карточки
    primary=(0.22, 0.87, 0.80, 1.0),   # основной акцент
    accent=(0.55, 0.62, 0.98, 1.0),    # доп. акцент
    button_color=(0.22, 0.87, 0.80, 1.0),
    text=(0.95, 0.96, 0.99, 1.0),
    text2=(0.75, 0.78, 0.86, 1.0),
)


def apply_to_app(app) -> None:
    # переносим цвета в app.mm_*, чтобы их использовал KV
    app.mm_bg = THEME.bg
    app.mm_surface = THEME.surface
    app.mm_surface2 = THEME.surface2
    app.mm_primary = THEME.primary
    app.mm_accent = THEME.accent
    app.mm_button_color = THEME.button_color
    app.mm_text = THEME.text
    app.mm_text2 = THEME.text2

    # стиль Material настраивается в main.py
