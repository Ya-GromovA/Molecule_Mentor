# /home/ulyashka_88/molecule-mentor/utils/visualizer_3d.py
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.widget import Widget

from .chem_types import Atom


@dataclass
class MoleculeGroup:
    # группа атомов которые можно вращать отдельно от остальных
    atom_indices: list[int] = field(default_factory=list)
    center: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rot_x: float = 0.0
    rot_y: float = 0.0
    scale: float = 1.0


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
    # простой 3D рендерер для молекул
    # умеет: вращать (свайпом), зумить (щипком или колёсиком)
    # рисует атомы шариками с тенями и бликами
    # можно тапать по атомам и связям в режиме редактирования
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.atoms: list[Atom] = []
        self.bonds: list[tuple[int, int]] = []
        self.highlight_break: set[tuple[int, int]] = set()
        self.highlight_form: set[tuple[int, int]] = set()

        # углы вращения и масштаб
        self._rot_x = 0.0
        self._rot_y = 0.0
        self._scale = 0.7  # начальный зум поменьше чтобы всё влезало
        self._center = (0.0, 0.0, 0.0)

        # сдвиг картинки если двумя пальцами таскать
        self._pan_x = 0.0
        self._pan_y = 0.0

        # если надо вращать молекулы по отдельности (для реакций)
        self._groups: list[MoleculeGroup] = []
        self._active_group_idx: Optional[int] = None  # какую сейчас крутим

        self._touches: dict[int, tuple[float, float]] = {}
        self._pinch_initial_dist: Optional[float] = None
        self._pinch_initial_scale: float = 1.0
        self._pinch_initial_mid: Optional[tuple[float, float]] = None
        self._pinch_group_idx: Optional[int] = None
        self._pinch_initial_group_scale: float = 1.0

        self._last_proj: list[tuple[float, float, float]] = []  # кеш проекций для тапов
        
        # режим редактирования (можно тапать по атомам и связям)
        self.edit_mode: bool = False
        self.on_atom_tap: Optional[callable] = None  # вызывается при тапе на атом
        self.on_bond_tap: Optional[callable] = None  # вызывается при тапе на связь
        self._touch_start_pos: Optional[tuple[float, float]] = None
        

        
        Clock.schedule_once(lambda *_: self.redraw(), 0)

    def set_scene(
        self,
        atoms: list[Atom],
        bonds: list[tuple[int, int]],
        highlight_break: Optional[list[tuple[int, int]]] = None,
        highlight_form: Optional[list[tuple[int, int]]] = None,
        groups: Optional[list[list[int]]] = None,
    ) -> None:
        # загружает молекулу для отображения
        # highlight_break - красным подсветить разрывающиеся связи
        # highlight_form - зелёным подсветить образующиеся связи
        # groups - если передать, то молекулы можно крутить по отдельности
        if not isinstance(atoms, list) or any(not isinstance(a, Atom) for a in atoms):
            raise TypeError("Visualizer3D accepts only List[Atom]")
        self.atoms = atoms
        self.bonds = bonds or []
        self.highlight_break = set(tuple(sorted(x)) for x in (highlight_break or []))
        self.highlight_form = set(tuple(sorted(x)) for x in (highlight_form or []))

        self._pan_x = 0.0
        self._pan_y = 0.0
        
        # разбиваем на группы если надо
        self._groups = []
        if groups:
            for atom_indices in groups:
                if atom_indices:
                    group = MoleculeGroup(atom_indices=atom_indices, scale=1.0)
                    self._recenter_group(group)
                    self._groups.append(group)
        
        self._active_group_idx = None
        self._recenter()
        self.redraw()
    
    def _recenter_group(self, group: MoleculeGroup) -> None:
        # считаем центр группы чтобы вращать вокруг него
        if not group.atom_indices:
            group.center = (0.0, 0.0, 0.0)
            return
        xs = [self.atoms[i].x for i in group.atom_indices if i < len(self.atoms)]
        ys = [self.atoms[i].y for i in group.atom_indices if i < len(self.atoms)]
        zs = [self.atoms[i].z for i in group.atom_indices if i < len(self.atoms)]
        if xs:
            group.center = (sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs))

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
        
        # если виджет ещё не инициализировался - пропускаем
        if self.width < 10 or self.height < 10:
            return super().on_touch_down(touch)
            
        # зум колёсиком мышки (на компе)
        if getattr(touch, "is_mouse_scrolling", False):
            direction = getattr(touch, "button", "")
            if direction == "scrolldown":
                self.zoom(-0.15)
            elif direction == "scrollup":
                self.zoom(+0.15)
            return True
        
        # запоминаем касание
        touch.grab(self)
        self._touches[touch.id] = touch.pos
        self._touch_start_pos = touch.pos
        
        # смотрим на какую молекулу ткнули
        if self._groups and len(self._touches) == 1:
            self._active_group_idx = self._find_group_at(touch.pos)

        if len(self._touches) == 2:
            pts = list(self._touches.values())
            self._pinch_initial_dist = math.dist(pts[0], pts[1])
            self._pinch_initial_scale = self._scale
            self._pinch_initial_mid = (
                (pts[0][0] + pts[1][0]) / 2.0,
                (pts[0][1] + pts[1][1]) / 2.0,
            )
            self._pinch_group_idx = None
            if self._groups:
                g0 = self._find_group_at(pts[0])
                g1 = self._find_group_at(pts[1])
                if g0 is not None and g0 == g1:
                    self._pinch_group_idx = g0
                    self._pinch_initial_group_scale = self._groups[g0].scale

        return True
    
    def _find_group_at(self, pos: tuple[float, float]) -> Optional[int]:
        # ищем какая молекула под пальцем
        if not self._last_proj or not self._groups:
            return None
        
        rel_x = pos[0] - self.x
        rel_y = pos[1] - self.y
        
        # Проверяем каждую группу
        for group_idx, group in enumerate(self._groups):
            for atom_idx in group.atom_indices:
                if atom_idx >= len(self._last_proj):
                    continue
                px, py, _ = self._last_proj[atom_idx]
                px -= self.x
                py -= self.y
                
                # область захвата побольше чтоб легче попадать
                r = dp(25)
                if (rel_x - px) ** 2 + (rel_y - py) ** 2 <= r * r:
                    return group_idx
        
        return None

    def on_touch_move(self, touch):
        # обрабатываем только свои касания
        if touch.grab_current is not self:
            return super().on_touch_move(touch)
        
        if touch.id not in self._touches:
            return super().on_touch_move(touch)

        prev = self._touches[touch.id]
        self._touches[touch.id] = touch.pos

        if len(self._touches) == 1:
            dx = touch.x - prev[0]
            dy = touch.y - prev[1]
            
            if self._groups and self._active_group_idx is not None:
                # крутим конкретную молекулу
                group = self._groups[self._active_group_idx]
                group.rot_y += dx * 0.012
                group.rot_x -= dy * 0.012
            else:
                # крутим всё вместе
                self._rot_y += dx * 0.008
                self._rot_x -= dy * 0.008
            
            self.redraw()
        elif len(self._touches) == 2 and self._pinch_initial_dist:
            pts = list(self._touches.values())
            d = math.dist(pts[0], pts[1])
            if d > 1e-3:
                factor = d / self._pinch_initial_dist
                if self._pinch_group_idx is not None and self._groups:
                    group = self._groups[self._pinch_group_idx]
                    group.scale = max(0.4, min(3.0, self._pinch_initial_group_scale * factor))
                else:
                    self._scale = max(0.15, min(4.0, self._pinch_initial_scale * factor))

            if self._pinch_initial_mid:
                mid = ((pts[0][0] + pts[1][0]) / 2.0, (pts[0][1] + pts[1][1]) / 2.0)
                dx = mid[0] - self._pinch_initial_mid[0]
                dy = mid[1] - self._pinch_initial_mid[1]
                self._pan_x += dx
                self._pan_y += dy
                # при движении двумя пальцами ещё немного наклоняем
                self._rot_x -= dy * 0.003
                self._rot_y += dx * 0.003
                self._pinch_initial_mid = mid

            self.redraw()

        return True

    def on_touch_up(self, touch):
        # отпустили палец
        if touch.grab_current is self:
            touch.ungrab(self)
        
        if touch.id in self._touches:
            self._touches.pop(touch.id, None)
        
        # проверяем не тап ли это (почти не двигали)
        if self.edit_mode and self._touch_start_pos:
            dx = abs(touch.pos[0] - self._touch_start_pos[0])
            dy = abs(touch.pos[1] - self._touch_start_pos[1])
            
            # если сдвинули меньше чем на 10dp - считаем тапом
            from kivy.metrics import dp as dp_func
            if dx < dp_func(10) and dy < dp_func(10):
                self._handle_tap(touch.pos)
        
        self._touch_start_pos = None
        self._active_group_idx = None
        
        if len(self._touches) < 2:
            self._pinch_initial_dist = None
            self._pinch_initial_mid = None
            self._pinch_group_idx = None
        return super().on_touch_up(touch)

    def _handle_tap(self, pos) -> None:
        # когда тапнули - проверяем попали ли на атом или связь
        if not self._last_proj:
            return
        
        rel_x = pos[0] - self.x
        rel_y = pos[1] - self.y
        
        # сначала проверяем атомы
        from kivy.metrics import dp as dp_func
        for idx, (px, py, _) in enumerate(self._last_proj):
            r = dp_func(18)  # область попадания
            dx = rel_x - (px - self.x)
            dy = rel_y - (py - self.y)
            if dx * dx + dy * dy <= r * r:
                if self.on_atom_tap:
                    self.on_atom_tap(idx)
                return
        
        # потом проверяем связи
        for (i, j) in self.bonds:
            if i >= len(self._last_proj) or j >= len(self._last_proj):
                continue
            
            xi, yi, _ = self._last_proj[i]
            xj, yj, _ = self._last_proj[j]
            
            # переводим в локальные координаты
            xi -= self.x
            yi -= self.y
            xj -= self.x
            yj -= self.y
            
            dist = self._point_to_line_dist(rel_x, rel_y, xi, yi, xj, yj)
            if dist < dp_func(12):
                if self.on_bond_tap:
                    self.on_bond_tap((i, j) if i < j else (j, i))
                return

    def _point_to_line_dist(self, px, py, x1, y1, x2, y2) -> float:
        # расстояние от точки до линии (для тапа по связи)
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5

    def zoom(self, delta: float) -> None:
        self._scale = max(0.15, min(4.0, self._scale + delta))
        self.redraw()

    def _project(self, x: float, y: float, z: float, atom_idx: Optional[int] = None) -> tuple[float, float, float]:
        # проецируем 3D координаты на экран
        # если атом в группе - сначала применяем вращение группы
        
        # ищем группу атома
        group = None
        if atom_idx is not None and self._groups:
            for g in self._groups:
                if atom_idx in g.atom_indices:
                    group = g
                    break
        
        if group:
            # вращаем относительно центра группы
            gcx, gcy, gcz = group.center
            lx, ly, lz = x - gcx, y - gcy, z - gcz

            # масштаб отдельной молекулы
            scale = getattr(group, "scale", 1.0)
            lx *= scale
            ly *= scale
            lz *= scale
            
            # применяем вращение
            cosx = math.cos(group.rot_x)
            sinx = math.sin(group.rot_x)
            ly2 = ly * cosx - lz * sinx
            lz2 = ly * sinx + lz * cosx
            ly, lz = ly2, lz2
            
            cosy = math.cos(group.rot_y)
            siny = math.sin(group.rot_y)
            lx2 = lx * cosy + lz * siny
            lz2 = -lx * siny + lz * cosy
            lx, lz = lx2, lz2
            
            # возвращаем в мировые координаты
            x, y, z = lx + gcx, ly + gcy, lz + gcz
        
        # сдвигаем к центру
        cx, cy, cz = self._center
        x -= cx
        y -= cy
        z -= cz

        # глобальное вращение всей сцены
        cosx = math.cos(self._rot_x)
        sinx = math.sin(self._rot_x)
        y2 = y * cosx - z * sinx
        z2 = y * sinx + z * cosx
        y, z = y2, z2

        cosy = math.cos(self._rot_y)
        siny = math.sin(self._rot_y)
        x2 = x * cosy + z * siny
        z2 = -x * siny + z * cosy
        x, z = x2, z2

        # масштабируем под размер виджета
        norm = 1.8
        sx = (x / norm) * (min(self.width, self.height) * 0.38) * self._scale
        sy = (y / norm) * (min(self.width, self.height) * 0.38) * self._scale

        px = self.center_x + sx + self._pan_x
        py = self.center_y + sy + self._pan_y
        depth = z
        return px, py, depth

    def redraw(self) -> None:
        self.canvas.clear()
        self.canvas.after.clear()

        # тёмный фон чтобы молекулы было видно
        with self.canvas:
            Color(0.08, 0.09, 0.12, 1.0)
            Rectangle(pos=self.pos, size=self.size)

        if not self.atoms:
            return

        # проецируем все атомы на 2D
        proj = [self._project(a.x, a.y, a.z, idx) for idx, a in enumerate(self.atoms)]
        self._last_proj = proj

        depths = [p[2] for p in proj]
        dmin, dmax = min(depths), max(depths)
        dr = (dmax - dmin) if (dmax - dmin) > 1e-6 else 1.0

        # сортируем чтобы дальние рисовались первыми
        order = sorted(range(len(proj)), key=lambda idx: proj[idx][2])
        
        with self.canvas:
            # сначала рисуем связи (палочки между атомами)
            for (i, j) in self.bonds:
                if i >= len(proj) or j >= len(proj):
                    continue
                xi, yi, di = proj[i]
                xj, yj, dj = proj[j]
                bond = (i, j) if i < j else (j, i)
                
                # толщина зависит от глубины
                avg_depth = (di + dj) / 2
                depth_factor = 0.7 + 0.6 * ((avg_depth - dmin) / dr) if dr > 0 else 1.0
                
                if bond in self.highlight_break:
                    Color(0.95, 0.30, 0.35, 1.0)
                    Line(points=[xi, yi, xj, yj], width=dp(2.5) * depth_factor)
                elif bond in self.highlight_form:
                    Color(0.22, 0.87, 0.80, 1.0)
                    Line(points=[xi, yi, xj, yj], width=dp(2.5) * depth_factor)
                else:
                    Color(0.55, 0.58, 0.65, 1.0)  # Непрозрачные связи
                    Line(points=[xi, yi, xj, yj], width=dp(1.8) * depth_factor)

            # потом рисуем атомы (шарики)
            for idx in order:
                x, y, depth = proj[idx]
                a = self.atoms[idx]

                # чем ближе атом тем он больше и ярче
                zn = (depth - dmin) / dr

                # размер шарика
                r = dp(11) * (0.80 + 0.35 * self._scale) * (0.88 + 0.24 * zn)

                base = _col(a.element)

                # тень под шариком
                Color(0.0, 0.0, 0.0, 0.25)
                Ellipse(pos=(x - r + dp(2), y - r - dp(2)), size=(2 * r, 2 * r))

                # сам шарик
                body_color = _mul_rgb(base, 0.70 + 0.30 * zn)
                Color(body_color[0], body_color[1], body_color[2], 1.0)
                Ellipse(pos=(x - r, y - r), size=(2 * r, 2 * r))

                # блик сверху (типа свет падает)
                Color(1.0, 1.0, 1.0, 0.28)
                highlight_r = r * 0.55
                Ellipse(pos=(x - r * 0.40, y + r * 0.10), size=(highlight_r, highlight_r * 0.9))

                # маленький яркий блик
                Color(1.0, 1.0, 1.0, 0.55)
                Ellipse(pos=(x - r * 0.25, y + r * 0.30), size=(r * 0.18, r * 0.16))

                # обводка
                Color(0.0, 0.0, 0.0, 0.65)
                Line(circle=(x, y, r), width=dp(1.0))

        # подписи элементов на атомах
        with self.canvas.after:
            for idx in order:
                x, y, depth = proj[idx]
                a = self.atoms[idx]
                zn = (depth - dmin) / dr
                
                # размер букв
                font_sz = dp(10) * (0.85 + 0.30 * zn) * (0.85 + 0.25 * self._scale)
                label = CoreLabel(text=a.element, font_size=font_sz, bold=True)
                label.refresh()
                tex = label.texture
                tw, th = tex.size
                
                # по центру атома
                tx = x - tw / 2
                ty = y - th / 2
                
                # тень текста
                Color(0.0, 0.0, 0.0, 0.60)
                Rectangle(texture=tex, pos=(tx + dp(0.8), ty - dp(0.8)), size=tex.size)
                
                # белый текст
                Color(1.0, 1.0, 1.0, 0.95)
                Rectangle(texture=tex, pos=(tx, ty), size=tex.size)
