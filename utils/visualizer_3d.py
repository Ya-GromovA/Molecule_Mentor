# /home/ulyashka_88/molecule-mentor/utils/visualizer_3d.py
from __future__ import annotations

import math
from typing import Optional

from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.widget import Widget

from .chem_types import Atom


_ELEMENT_COLOR = {
    "H": (0.92, 0.92, 0.95, 1.0),
    "C": (0.35, 0.35, 0.40, 1.0),
    "N": (0.35, 0.50, 0.95, 1.0),
    "O": (0.95, 0.30, 0.35, 1.0),
    "S": (0.95, 0.85, 0.25, 1.0),
    "P": (0.95, 0.55, 0.25, 1.0),
    "Cl": (0.35, 0.95, 0.55, 1.0),
    "Na": (0.60, 0.55, 0.95, 1.0),
    "K": (0.70, 0.45, 0.95, 1.0),
}


def _col(element: str) -> tuple[float, float, float, float]:
    return _ELEMENT_COLOR.get(element, (0.70, 0.75, 0.85, 1.0))


def _mul_rgb(rgba, k: float):
    r, g, b, a = rgba
    return (min(1.0, r * k), min(1.0, g * k), min(1.0, b * k), a)


class Visualizer3D(Widget):
    """
    Lightweight 3D-ish renderer:
    - accepts ONLY Atom objects (requirement)
    - supports rotate (drag) + zoom (pinch or wheel)
    - adds simple "volume": shadow + highlight + depth shading
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.atoms: list[Atom] = []
        self.bonds: list[tuple[int, int]] = []
        self.highlight_break: set[tuple[int, int]] = set()
        self.highlight_form: set[tuple[int, int]] = set()

        self._rot_x = 0.0
        self._rot_y = 0.0
        self._scale = 1.0
        self._center = (0.0, 0.0, 0.0)

        self._touches: dict[int, tuple[float, float]] = {}
        self._pinch_initial_dist: Optional[float] = None
        self._pinch_initial_scale: float = 1.0

        self._last_proj: list[tuple[float, float, float]] = []  # (x,y,depth)
        Clock.schedule_once(lambda *_: self.redraw(), 0)

    def set_scene(
        self,
        atoms: list[Atom],
        bonds: list[tuple[int, int]],
        highlight_break: Optional[list[tuple[int, int]]] = None,
        highlight_form: Optional[list[tuple[int, int]]] = None,
    ) -> None:
        if not isinstance(atoms, list) or any(not isinstance(a, Atom) for a in atoms):
            raise TypeError("Visualizer3D accepts only List[Atom]")
        self.atoms = atoms
        self.bonds = bonds or []
        self.highlight_break = set(tuple(sorted(x)) for x in (highlight_break or []))
        self.highlight_form = set(tuple(sorted(x)) for x in (highlight_form or []))
        self._recenter()
        self.redraw()

    def _recenter(self) -> None:
        if not self.atoms:
            self._center = (0.0, 0.0, 0.0)
            return
        xs = [a.x for a in self.atoms]
        ys = [a.y for a in self.atoms]
        zs = [a.z for a in self.atoms]
        self._center = (sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs))

    def on_size(self, *_):
        self.redraw()

    def on_pos(self, *_):
        self.redraw()

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
            
        # Wheel zoom for desktop
        if getattr(touch, "is_mouse_scrolling", False):
            direction = getattr(touch, "button", "")
            if direction == "scrolldown":
                self.zoom(-0.15)
            elif direction == "scrollup":
                self.zoom(+0.15)
            return True

        self._touches[touch.id] = touch.pos

        if len(self._touches) == 2:
            pts = list(self._touches.values())
            self._pinch_initial_dist = math.dist(pts[0], pts[1])
            self._pinch_initial_scale = self._scale

        return True

    def on_touch_move(self, touch):
        if touch.id not in self._touches:
            return super().on_touch_move(touch)

        prev = self._touches[touch.id]
        self._touches[touch.id] = touch.pos

        if len(self._touches) == 1:
            dx = touch.x - prev[0]
            dy = touch.y - prev[1]
            self._rot_y += dx * 0.008
            self._rot_x -= dy * 0.008
            self.redraw()
        elif len(self._touches) == 2 and self._pinch_initial_dist:
            pts = list(self._touches.values())
            d = math.dist(pts[0], pts[1])
            if d > 1e-3:
                factor = d / self._pinch_initial_dist
                self._scale = max(0.35, min(4.0, self._pinch_initial_scale * factor))
                self.redraw()

        return True

    def on_touch_up(self, touch):
        if touch.id in self._touches:
            self._touches.pop(touch.id, None)
        if len(self._touches) < 2:
            self._pinch_initial_dist = None
        return super().on_touch_up(touch)

    def zoom(self, delta: float) -> None:
        self._scale = max(0.35, min(4.0, self._scale + delta))
        self.redraw()

    def _project(self, x: float, y: float, z: float) -> tuple[float, float, float]:
        cx, cy, cz = self._center
        x -= cx
        y -= cy
        z -= cz

        # rotate x
        cosx = math.cos(self._rot_x)
        sinx = math.sin(self._rot_x)
        y2 = y * cosx - z * sinx
        z2 = y * sinx + z * cosx
        y, z = y2, z2

        # rotate y
        cosy = math.cos(self._rot_y)
        siny = math.sin(self._rot_y)
        x2 = x * cosy + z * siny
        z2 = -x * siny + z * cosy
        x, z = x2, z2

        # scale and fit to widget
        norm = 1.8
        sx = (x / norm) * (min(self.width, self.height) * 0.38) * self._scale
        sy = (y / norm) * (min(self.width, self.height) * 0.38) * self._scale

        px = self.center_x + sx
        py = self.center_y + sy
        depth = z
        return px, py, depth

    def redraw(self) -> None:
        self.canvas.clear()
        self.canvas.after.clear()

        # фон виджета (тёмный, чтобы не выглядел “плоско на сером”)
        with self.canvas:
            Color(0.08, 0.09, 0.12, 1.0)
            Rectangle(pos=self.pos, size=self.size)

        if not self.atoms:
            return

        proj = [self._project(a.x, a.y, a.z) for a in self.atoms]
        self._last_proj = proj

        depths = [p[2] for p in proj]
        dmin, dmax = min(depths), max(depths)
        dr = (dmax - dmin) if (dmax - dmin) > 1e-6 else 1.0

        with self.canvas:
            # bonds
            for (i, j) in self.bonds:
                if i >= len(proj) or j >= len(proj):
                    continue
                xi, yi, _ = proj[i]
                xj, yj, _ = proj[j]
                bond = (i, j) if i < j else (j, i)
                if bond in self.highlight_break:
                    Color(0.95, 0.30, 0.35, 1.0)
                    Line(points=[xi, yi, xj, yj], width=dp(2.2))
                elif bond in self.highlight_form:
                    Color(0.22, 0.87, 0.80, 1.0)
                    Line(points=[xi, yi, xj, yj], width=dp(2.2))
                else:
                    Color(0.70, 0.75, 0.85, 0.45)
                    Line(points=[xi, yi, xj, yj], width=dp(1.6))

            # atoms (front last)
            order = sorted(range(len(proj)), key=lambda idx: proj[idx][2])
            for idx in order:
                x, y, depth = proj[idx]
                a = self.atoms[idx]

                # depth normalize: 0..1
                zn = (depth - dmin) / dr

                # размер: слегка больше для “ближе к камере”
                r = dp(10) * (0.80 + 0.35 * self._scale) * (0.92 + 0.20 * zn)

                base = _col(a.element)

                # тень
                Color(0.0, 0.0, 0.0, 0.22)
                Ellipse(pos=(x - r + dp(2), y - r - dp(2)), size=(2 * r, 2 * r))

                # сам шарик: чуть яркость зависит от глубины
                Color(*_mul_rgb(base, 0.85 + 0.25 * zn))
                Ellipse(pos=(x - r, y - r), size=(2 * r, 2 * r))

                # блик
                Color(1.0, 1.0, 1.0, 0.18)
                Ellipse(pos=(x - r * 0.35, y + r * 0.05), size=(r * 0.55, r * 0.55))

                # обводка
                Color(0.05, 0.06, 0.08, 0.85)
                Line(circle=(x, y, r), width=dp(1.2))

        # labels overlay
        with self.canvas.after:
            for idx, (x, y, _) in enumerate(proj):
                a = self.atoms[idx]
                label = CoreLabel(text=a.element, font_size=dp(12))
                label.refresh()
                tex = label.texture
                tw, th = tex.size
                Color(0.0, 0.0, 0.0, 0.35)
                Rectangle(pos=(x + dp(8), y + dp(8)), size=(tw + dp(6), th + dp(4)))
                Color(0.90, 0.92, 0.98, 0.95)
                Rectangle(texture=tex, pos=(x + dp(11), y + dp(10)), size=tex.size)
