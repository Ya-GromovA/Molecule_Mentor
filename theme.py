from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

RGBA = Tuple[float, float, float, float]


@dataclass(frozen=True)
class AppTheme:
    # Material 3 friendly palette (Tiffany + light blue-violet)
    bg: RGBA
    surface: RGBA
    surface2: RGBA
    primary: RGBA
    accent: RGBA
    text: RGBA
    text2: RGBA


THEME = AppTheme(
    bg=(0.06, 0.07, 0.10, 1.0),        # deep indigo-ish
    surface=(0.10, 0.12, 0.18, 1.0),   # card background
    surface2=(0.13, 0.16, 0.24, 1.0),  # elevated card
    primary=(0.22, 0.87, 0.80, 1.0),   # tiffany
    accent=(0.55, 0.62, 0.98, 1.0),    # light blue-violet
    text=(0.95, 0.96, 0.99, 1.0),
    text2=(0.75, 0.78, 0.86, 1.0),
)


def apply_to_app(app) -> None:
    """
    Public, stable API:
    - Sets app.mm_* color attributes used from KV.
    - Does not touch deprecated KivyMD APIs.
    """
    app.mm_bg = THEME.bg
    app.mm_surface = THEME.surface
    app.mm_surface2 = THEME.surface2
    app.mm_primary = THEME.primary
    app.mm_accent = THEME.accent
    app.mm_text = THEME.text
    app.mm_text2 = THEME.text2

    # Material style is configured in app (main.py): theme_cls.material_style="M3"
    # Here we only provide explicit RGBA colors for KV.
