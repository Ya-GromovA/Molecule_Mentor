from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Tuple

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemSupportingText
from kivymd.uix.scrollview import MDScrollView

from .base_screen import BaseScreen
from utils.reaction_repo import ReactionRepo
from utils.chem_types import Reaction
from utils.visualizer_3d import Visualizer3D


@dataclass
class _PlayerState:
    playing: bool = False
    frame_idx: int = 0
    tick_ev: Optional[object] = None  # таймер проигрывания


class ReactionViewerScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Реакция"
        self._repo: Optional[ReactionRepo] = None
        self._rxn: Optional[Reaction] = None
        self._viz: Optional[Visualizer3D] = None
        self._state = _PlayerState()

        self._lbl_name: Optional[MDLabel] = None
        self._lbl_eq: Optional[MDLabel] = None
        self._lbl_step_title: Optional[MDLabel] = None
        self._lbl_step_desc: Optional[MDLabel] = None
        self._btn_play: Optional[MDButton] = None
        self._btn_play_text: Optional[MDButtonText] = None

    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        Clock.schedule_once(lambda *_: self._build(), 0)
        Clock.schedule_once(lambda *_: self._load_from_nav(), 0)

    def on_pre_leave(self, *args):
        self._stop()
        return super().on_pre_leave(*args)
        
    # ---------- помощники для UI ----------
    def _make_btn(self, label: str, on_release, bg_rgba=None):
        btn = MDButton(
            style="filled",
            on_release=on_release,
            size_hint_y=None,
            height=dp(44),
        )
        if bg_rgba is not None:
            btn.md_bg_color = bg_rgba
            btn.theme_bg_color = "Custom"
        txt = MDButtonText(text=label, font_size=dp(16))
        btn.add_widget(txt)
        return btn, txt
        
    # ---------- геометрия ----------
    def _separate_molecules(self, atoms: List[Dict], bonds: List) -> Tuple[List[Dict], List[List[int]]]:
        # раздвигаем молекулы, чтобы они не налезали друг на друга
        if not atoms:
            return atoms, []
        if not bonds:
            # если связей нет, каждый атом отдельная группа
            return atoms, [[i] for i in range(len(atoms))]

        n = len(atoms)
        adj: List[List[int]] = [[] for _ in range(n)]
        for b in bonds:
            try:
                i, j = int(b[0]), int(b[1])
            except Exception:
                continue
            if 0 <= i < n and 0 <= j < n and i != j:
                adj[i].append(j)
                adj[j].append(i)

        # ищем компоненты связности
        seen = [False] * n
        comps: List[List[int]] = []
        for start in range(n):
            if seen[start]:
                continue
            stack = [start]
            seen[start] = True
            comp: List[int] = []
            while stack:
                v = stack.pop()
                comp.append(v)
                for u in adj[v]:
                    if not seen[u]:
                        seen[u] = True
                        stack.append(u)
            comps.append(comp)

        # если группа одна, двигать не надо
        if len(comps) <= 1:
            return atoms, comps

        def _get(a, key: str, default=0.0):
            # атомы могут быть dict или объектом
            if isinstance(a, dict):
                return a.get(key, default)
            return getattr(a, key, default)

        def bbox(idxs: List[int]) -> Tuple[float, float, float, float, float, float]:
            xs = [float(_get(atoms[k], "x", 0.0)) for k in idxs]
            ys = [float(_get(atoms[k], "y", 0.0)) for k in idxs]
            zs = [float(_get(atoms[k], "z", 0.0)) for k in idxs]
            return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)

        # сортируем слева направо, чтобы порядок был стабильный
        comp_meta = []
        for c in comps:
            x0, x1, y0, y1, z0, z1 = bbox(c)
            cx = (x0 + x1) / 2.0
            width = max(x1 - x0, y1 - y0, z1 - z0)
            comp_meta.append((cx, width, c, (x0, x1)))

        comp_meta.sort(key=lambda t: t[0])

        # раскладываем молекулы по оси X
        shifts_x: Dict[int, float] = {}
        shifts_y: Dict[int, float] = {}  # всегда 0
        
        prev_right = None
        
        for cx, width, comp, (x0, x1) in comp_meta:
            w = max(width, 0.5)
            gap = max(0.3, w * 0.20)  # небольшой зазор
            
            if prev_right is None:
                # первая молекула около нуля
                shift_x = -cx
                prev_right = x1 + shift_x
            else:
                # следующую ставим правее
                target_left = prev_right + gap
                shift_x = target_left - x0
                prev_right = x1 + shift_x
            
            for k in comp:
                shifts_x[k] = shift_x
                shifts_y[k] = 0.0  # все на одной высоте

        # применяем сдвиги (делаем копию)
        out = []
        AtomCls = atoms[0].__class__ if atoms else None

        for i, a in enumerate(atoms):
            sx = float(shifts_x.get(i, 0.0))
            sy = float(shifts_y.get(i, 0.0))

            # dict атомы
            if isinstance(a, dict):
                aa = dict(a)
                aa["x"] = float(aa.get("x", 0.0)) + sx
                aa["y"] = float(aa.get("y", 0.0)) + sy
                out.append(aa)
                continue

            # обычный объект Atom
            try:
                kwargs = {
                    "element": getattr(a, "element", None),
                    "x": float(getattr(a, "x", 0.0)) + sx,
                    "y": float(getattr(a, "y", 0.0)) + sy,
                    "z": float(getattr(a, "z", 0.0)),
                    "label": getattr(a, "label", None),
                }
                # если label=None, то убираем
                if kwargs["label"] is None:
                    kwargs.pop("label", None)

                out.append(AtomCls(**kwargs))
            except Exception:
                try:
                    setattr(a, "x", float(getattr(a, "x", 0.0)) + sx)
                    setattr(a, "y", float(getattr(a, "y", 0.0)) + sy)
                except Exception:
                    pass
                out.append(a)

        # центрируем сцену по X
        def _get_x(a):
            if isinstance(a, dict):
                return float(a.get("x", 0.0))
            return float(getattr(a, "x", 0.0))

        xs_all = [_get_x(a) for a in out]
        cx_all = (min(xs_all) + max(xs_all)) / 2.0

        if abs(cx_all) > 1e-6:
            for a in out:
                if isinstance(a, dict):
                    a["x"] = float(a.get("x", 0.0)) - cx_all
                else:
                    try:
                        setattr(a, "x", float(getattr(a, "x", 0.0)) - cx_all)
                    except Exception:
                        pass

        # возвращаем атомы и группы
        sorted_groups = [comp for (_, _, comp, _) in comp_meta]
        return out, sorted_groups

    def _build(self) -> None:
        app = self.get_app()
        self.clear_widgets()

        root = BoxLayout(orientation="vertical", padding=dp(6), spacing=dp(4))

        # заголовок сверху
        from kivy.metrics import sp
        
        self._lbl_name = MDLabel(
            text="",
            bold=True,
            theme_text_color="Custom",
            text_color=app.mm_text,
            halign="left",
            size_hint_y=None,
            height=dp(24),
            font_size=sp(16),  # масштабируемый шрифт
            shorten=True,
            shorten_from="right",
            text_size=(None, None),
        )
        self._lbl_eq = MDLabel(
            text="",
            theme_text_color="Custom",
            text_color=app.mm_text2,
            halign="left",
            size_hint_y=None,
            height=dp(18),
            font_size=sp(12),  # масштабируемый шрифт
            shorten=True,
            shorten_from="right",
        )
        
        # ширина текста под ширину родителя
        def _update_text_size(*_):
            if self._lbl_name:
                self._lbl_name.text_size = (root.width - dp(20), None)
            if self._lbl_eq:
                self._lbl_eq.text_size = (root.width - dp(20), None)
        root.bind(width=_update_text_size)

        root.add_widget(self._lbl_name)
        root.add_widget(self._lbl_eq)

        # тело: 3D сверху, кнопки снизу
        body = BoxLayout(orientation="vertical", size_hint=(1, 1), spacing=dp(4))

        # 3D область
        host = BoxLayout(orientation="vertical", size_hint=(1, 0.75))
        self._viz = Visualizer3D(size_hint=(1, 1))
        host.add_widget(self._viz)

        # нижняя панель с кнопками и шагами
        bottom = BoxLayout(orientation="vertical", size_hint=(1, 0.25), spacing=dp(4))

        # кнопки управления
        controls = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(46), spacing=dp(6))

        bg_ctrl = app.mm_surface2
        bg_play = app.mm_accent

        btn_first, _ = self._make_btn("|<", lambda *_: self._go_first(), bg_ctrl)
        btn_prev, _ = self._make_btn("<", lambda *_: self._go_prev(), bg_ctrl)
        self._btn_play, self._btn_play_text = self._make_btn("Play", lambda *_: self._toggle_play(), bg_play)
        btn_next, _ = self._make_btn(">", lambda *_: self._go_next(), bg_ctrl)
        btn_last, _ = self._make_btn(">|", lambda *_: self._go_last(), bg_ctrl)

        for b in (btn_first, btn_prev, self._btn_play, btn_next, btn_last):
            b.size_hint_x = 1
            controls.add_widget(b)

        # блок с описанием шага
        from kivy.metrics import sp
        
        step_box = BoxLayout(orientation="vertical", size_hint=(1, 1), spacing=dp(2))

        self._lbl_step_title = MDLabel(
            text="",
            bold=True,
            theme_text_color="Custom",
            text_color=app.mm_text,
            halign="left",
            size_hint_y=None,
            height=dp(20),
            font_size=sp(14),  # масштабируемый шрифт
        )

        self._lbl_step_desc = MDLabel(
            text="",
            theme_text_color="Custom",
            text_color=app.mm_text2,
            halign="left",
            valign="top",
            font_size=sp(13),  # масштабируемый шрифт
            text_size=(0, None),
            size_hint_y=None,
        )
        
        # высота по содержимому
        self._lbl_step_desc.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))

        desc_scroll = MDScrollView(do_scroll_x=False, bar_width=dp(4))
        desc_scroll.add_widget(self._lbl_step_desc)

        step_box.add_widget(self._lbl_step_title)
        step_box.add_widget(desc_scroll)

        bottom.add_widget(controls)
        bottom.add_widget(step_box)

        body.add_widget(host)
        body.add_widget(bottom)

        root.add_widget(body)

        
        self.add_widget(root)

        # обновляем text_size при ресайзе
        def _fix_text_size(*_):
            if self._lbl_step_desc:
                self._lbl_step_desc.text_size = (root.width - dp(20), None)

        self.bind(size=_fix_text_size)
        _fix_text_size()

    def _load_from_nav(self) -> None:
        app = self.get_app()
        reaction_id = (app.nav_state or {}).get("reaction_id")
        if not reaction_id:
            app.toast("Не передан reaction_id")
            return

        self._repo = ReactionRepo(app.reactions_dir)

        try:
            self._rxn = self._repo.load_reaction(str(reaction_id))
        except Exception as e:
            Logger.exception(f"[ReactionViewer] load failed: {e}")
            app.toast(f"Ошибка загрузки реакции: {e}")
            return

        # сброс состояния плеера
        self._stop()
        self._state.frame_idx = 0

        self._render_static()
        self._render_frame()

    def _render_static(self) -> None:
        if not self._rxn:
            return
        if self._lbl_name:
            self._lbl_name.text = self._rxn.meta.name
        if self._lbl_eq:
            self._lbl_eq.text = self._rxn.meta.equation or ""

    def _current_step_index(self) -> int:
        if not self._rxn or not self._rxn.frames:
            return 0
        idx = max(0, min(self._state.frame_idx, len(self._rxn.frames) - 1))
        steps = self._rxn.steps or []
        frame = self._rxn.frames[idx]

        stage_idx = None
        try:
            if frame.stage_index is not None:
                stage_idx = int(frame.stage_index)
        except Exception:
            stage_idx = None

        if not steps:
            return int(stage_idx or 0)

        if not self._uses_stage_index():
            total = max(len(self._rxn.frames) - 1, 1)
            return int(round((idx / total) * (len(steps) - 1)))

        if stage_idx is None:
            total = max(len(self._rxn.frames) - 1, 1)
            return int(round((idx / total) * (len(steps) - 1)))

        return max(0, min(stage_idx, len(steps) - 1))

    def _uses_stage_index(self) -> bool:
        if not self._rxn or not self._rxn.frames:
            return False
        try:
            max_stage = max(int(getattr(fr, "stage_index", 0) or 0) for fr in self._rxn.frames)
            min_stage = min(int(getattr(fr, "stage_index", 0) or 0) for fr in self._rxn.frames)
            return max_stage > min_stage
        except Exception:
            return False

    def _max_stage_index(self) -> int:
        if not self._rxn or not self._rxn.frames:
            return 0
        steps = self._rxn.steps or []
        if steps and not self._uses_stage_index():
            return max(0, len(steps) - 1)
        try:
            return max(int(getattr(fr, "stage_index", 0) or 0) for fr in self._rxn.frames)
        except Exception:
            return 0

    def _find_frame_for_stage(self, target_stage: int, direction: int = 0) -> int:
        if not self._rxn or not self._rxn.frames:
            return 0

        steps = self._rxn.steps or []
        if steps and not self._uses_stage_index():
            total = max(len(self._rxn.frames) - 1, 1)
            denom = max(len(steps) - 1, 1)
            return int(round((target_stage / denom) * total))

        for i, fr in enumerate(self._rxn.frames):
            try:
                if int(getattr(fr, "stage_index", 0) or 0) == target_stage:
                    return i
            except Exception:
                continue

        if direction < 0:
            for i in range(len(self._rxn.frames) - 1, -1, -1):
                try:
                    if int(getattr(self._rxn.frames[i], "stage_index", 0) or 0) < target_stage:
                        return i
                except Exception:
                    continue
        if direction > 0:
            for i, fr in enumerate(self._rxn.frames):
                try:
                    if int(getattr(fr, "stage_index", 0) or 0) > target_stage:
                        return i
                except Exception:
                    continue

        return max(0, min(self._state.frame_idx, len(self._rxn.frames) - 1))

    def _render_step(self) -> None:
        if not self._rxn:
            return
        si = self._current_step_index()
        steps = self._rxn.steps or []
        title = ""
        desc = ""
        if 0 <= si < len(steps):
            title = str(steps[si].get("title") or f"Шаг {si + 1}")
            desc = str(steps[si].get("description") or "")
        else:
            title = f"Шаг {si + 1}"
            desc = ""

        if self._lbl_step_title:
            self._lbl_step_title.text = title
        if self._lbl_step_desc:
            self._lbl_step_desc.text = desc

    def _render_frame(self) -> None:
        if not self._rxn or not self._viz:
            return
        if not self._rxn.frames:
            return

        idx = max(0, min(self._state.frame_idx, len(self._rxn.frames) - 1))
        fr = self._rxn.frames[idx]
        atoms = fr.atoms
        groups = None
        try:
            atoms, groups = self._separate_molecules(fr.atoms, fr.bonds)
        except Exception as e:
            Logger.exception(f"[ReactionViewer] separate_molecules failed: {e}")

        self._viz.set_scene(
            atoms=atoms,
            bonds=fr.bonds,
            highlight_break=fr.highlight_break,
            highlight_form=fr.highlight_form,
            groups=groups,  # группы для независимого вращения
        )
        self._render_step()

    # --- управление проигрыванием ---
    def _stop(self) -> None:
        self._state.playing = False
        if self._state.tick_ev is not None:
            try:
                self._state.tick_ev.cancel()
            except Exception:
                pass
        self._state.tick_ev = None
        if self._btn_play_text:
           self._btn_play_text.text = "Play"

    def _toggle_play(self) -> None:
        if not self._rxn or not self._rxn.frames:
            return
        if self._state.playing:
            self._stop()
            return

        self._state.playing = True
        if self._btn_play_text:
           self._btn_play_text.text = "Pause"

        fps = max(1, int(self._rxn.meta.fps or 12))
        dt = 1.0 / float(fps)

        def tick(_dt):
            if not self._state.playing:
                return
            self._state.frame_idx += 1
            if self._state.frame_idx >= len(self._rxn.frames):
                self._state.frame_idx = len(self._rxn.frames) - 1
                self._stop()
                return
            self._render_frame()

        self._state.tick_ev = Clock.schedule_interval(tick, dt)

    def _go_first(self) -> None:
        if not self._rxn or not self._rxn.frames:
            return
        self._stop()
        self._state.frame_idx = 0
        self._render_frame()

    def _go_last(self) -> None:
        if not self._rxn or not self._rxn.frames:
            return
        self._stop()
        self._state.frame_idx = len(self._rxn.frames) - 1
        self._render_frame()

    def _go_prev(self) -> None:
        if not self._rxn or not self._rxn.frames:
            return
        self._stop()
        current_step = self._current_step_index()
        target_step = max(0, current_step - 1)
        self._state.frame_idx = self._find_frame_for_stage(target_step, direction=-1)
        self._render_frame()

    def _go_next(self) -> None:
        if not self._rxn or not self._rxn.frames:
            return
        self._stop()
        current_step = self._current_step_index()
        max_stage = self._max_stage_index()
        target_step = min(max_stage, current_step + 1)
        self._state.frame_idx = self._find_frame_for_stage(target_step, direction=1)
        self._render_frame()
