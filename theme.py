from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

RGBA = Tuple[float, float, float, float]


@dataclass(frozen=True)
class AppTheme:

    bg: RGBA
    surface: RGBA
    surface2: RGBA
    primary: RGBA
    accent: RGBA
    button_color: RGBA
    text: RGBA
    text2: RGBA


THEME = AppTheme(
    bg=(0.11, 0.14, 0.24, 1.0),
    surface=(0.21, 0.19, 0.30, 1.0),
    surface2=(0.25, 0.23, 0.35, 1.0),
    primary=(0.22, 0.87, 0.80, 1.0),
    accent=(0.64, 0.58, 0.90, 1.0),
    button_color=(0.22, 0.87, 0.80, 1.0),
    text=(0.95, 0.96, 0.99, 1.0),
    text2=(0.82, 0.83, 0.90, 1.0),
)


def apply_to_app(app) -> None:

    app.mm_bg = THEME.bg
    app.mm_surface = THEME.surface
    app.mm_surface2 = THEME.surface2
    app.mm_primary = THEME.primary
    app.mm_accent = THEME.accent
    app.mm_button_color = THEME.button_color
    app.mm_text = THEME.text
    app.mm_text2 = THEME.text2
