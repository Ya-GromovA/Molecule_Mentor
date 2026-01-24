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
    tick_ev: Optional[object] = None  # ClockEvent


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
        
     # ---------- UI helpers (KivyMD 2.x safe) ----------
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
        
    # ---------- geometry helpers ----------
    def _separate_molecules(self, atoms: List[Dict], bonds: List) -> Tuple[List[Dict], List[List[int]]]:
        """
        Раздвигает отдельные молекулы/ионы внутри сцены, чтобы не накладывались.
        Молекула = связная компонента графа связей.
        Индексы атомов сохраняются.
        
        Returns:
            Tuple[atoms, groups] - атомы и список групп для независимого вращения
        """
        if not atoms:
            return atoms, []
        if not bonds:
            # Каждый атом — отдельная группа
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

        # найти компоненты связности (DFS/BFS)
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

        # Если реально одна компонента — раздвигать нечего, но группу создаём
        if len(comps) <= 1:
            return atoms, comps

        def _get(a, key: str, default=0.0):
            # atoms can be dicts OR Atom-like objects with attributes x/y/z
            if isinstance(a, dict):
                return a.get(key, default)
            return getattr(a, key, default)

        def bbox(idxs: List[int]) -> Tuple[float, float, float, float, float, float]:
            xs = [float(_get(atoms[k], "x", 0.0)) for k in idxs]
            ys = [float(_get(atoms[k], "y", 0.0)) for k in idxs]
            zs = [float(_get(atoms[k], "z", 0.0)) for k in idxs]
            return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)

        # Сортируем молекулы слева-направо по их центру (чтобы было стабильно)
        comp_meta = []
        for c in comps:
            x0, x1, y0, y1, z0, z1 = bbox(c)
            cx = (x0 + x1) / 2.0
            width = max(x1 - x0, y1 - y0, z1 - z0)
            comp_meta.append((cx, width, c, (x0, x1)))

        comp_meta.sort(key=lambda t: t[0])

        # Раскладываем молекулы ТОЛЬКО по оси X (в один ряд)
        shifts_x: Dict[int, float] = {}
        shifts_y: Dict[int, float] = {}  # всегда 0
        
        prev_right = None
        
        for cx, width, comp, (x0, x1) in comp_meta:
            w = max(width, 0.5)
            gap = max(0.3, w * 0.20)  # компактный зазор
            
            if prev_right is None:
                # Первая молекула: центрируем около 0
                shift_x = -cx
                prev_right = x1 + shift_x
            else:
                # Следующая: ставим правее предыдущей
                target_left = prev_right + gap
                shift_x = target_left - x0
                prev_right = x1 + shift_x
            
            for k in comp:
                shifts_x[k] = shift_x
                shifts_y[k] = 0.0  # Все на одной высоте

        # применяем сдвиги (копию атомов, оригинал не трогаем)
        out = []
        AtomCls = atoms[0].__class__ if atoms else None

        for i, a in enumerate(atoms):
            sx = float(shifts_x.get(i, 0.0))
            sy = float(shifts_y.get(i, 0.0))

            # dict atoms
            if isinstance(a, dict):
                aa = dict(a)
                aa["x"] = float(aa.get("x", 0.0)) + sx
                aa["y"] = float(aa.get("y", 0.0)) + sy
                out.append(aa)
                continue

            # Atom-like object: try to create a new instance; fallback to in-place update
            try:
                kwargs = {
                    "element": getattr(a, "element", None),
                    "x": float(getattr(a, "x", 0.0)) + sx,
                    "y": float(getattr(a, "y", 0.0)) + sy,
                    "z": float(getattr(a, "z", 0.0)),
                    "label": getattr(a, "label", None),
                }
                # some Atom classes may not accept label=None
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

        # Центрируем сцену по X (чтобы не "уезжала" камера)
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

        # Возвращаем атомы и группы (компоненты связности)
        sorted_groups = [comp for (_, _, comp, _) in comp_meta]
        return out, sorted_groups

    def _build(self) -> None:
        app = self.get_app()
        self.clear_widgets()

        root = BoxLayout(orientation="vertical", padding=dp(6), spacing=dp(4))

        # Header info - компактный заголовок
        from kivy.metrics import sp
        
        self._lbl_name = MDLabel(
            text="",
            bold=True,
            theme_text_color="Custom",
            text_color=app.mm_text,
            halign="left",
            size_hint_y=None,
            height=dp(24),
            font_size=sp(16),  # Масштабируемый шрифт
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
            font_size=sp(12),  # Масштабируемый шрифт
            shorten=True,
            shorten_from="right",
        )
        
        # Привязываем ширину текста к ширине родителя
        def _update_text_size(*_):
            if self._lbl_name:
                self._lbl_name.text_size = (root.width - dp(20), None)
            if self._lbl_eq:
                self._lbl_eq.text_size = (root.width - dp(20), None)
        root.bind(width=_update_text_size)

        root.add_widget(self._lbl_name)
        root.add_widget(self._lbl_eq)

        # --- BODY: 3D (больше) + нижняя панель (компактнее) ---
        body = BoxLayout(orientation="vertical", size_hint=(1, 1), spacing=dp(4))

        # 3D host — основная область (75% высоты)
        host = BoxLayout(orientation="vertical", size_hint=(1, 0.75))
        self._viz = Visualizer3D(size_hint=(1, 1))
        host.add_widget(self._viz)

        # Bottom panel — кнопки + шаг/описание (25%)
        bottom = BoxLayout(orientation="vertical", size_hint=(1, 0.25), spacing=dp(4))

        # Controls row — кнопки управления
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

        # Step info — занимает остаток нижней панели, описание скроллится
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
            font_size=sp(14),  # Масштабируемый шрифт
        )

        self._lbl_step_desc = MDLabel(
            text="",
            theme_text_color="Custom",
            text_color=app.mm_text2,
            halign="left",
            valign="top",
            font_size=sp(13),  # Масштабируемый шрифт
            text_size=(0, None),
            size_hint_y=None,
        )
        
        # Автоматическая высота по контенту
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

        # обновлять text_size при ресайзе
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

        # reset player state
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
        return int(self._rxn.frames[idx].stage_index or 0)

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
            groups=groups,  # Передаём группы для независимого вращения
        )
        self._render_step()

    # --- player controls ---
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
        self._state.frame_idx = max(0, self._state.frame_idx - 1)
        self._render_frame()

    def _go_next(self) -> None:
        if not self._rxn or not self._rxn.frames:
            return
        self._stop()
        self._state.frame_idx = min(len(self._rxn.frames) - 1, self._state.frame_idx + 1)
        self._render_frame()
