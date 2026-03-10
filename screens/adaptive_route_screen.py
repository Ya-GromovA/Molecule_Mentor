from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout

from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView

from .base_screen import BaseScreen
from .marquee_label import MarqueeLabel


@dataclass(frozen=True)
class RouteItem:
    section_id: int
    section_title: str
    avg_percent: float
    best_percent: float
    attempts: int
    reaction_id: str
    reaction_title: str


REACTION_BY_SECTION: dict[int, tuple[str, str]] = {
    1: ("combustion_methane", "Горение метана"),
    2: ("hydration_ethene", "Гидратация этилена"),
    3: ("esterification_acetic_ethanol", "Этерификация"),
    4: ("acid_base_nh3_hcl", "Кислотно-основное взаимодействие"),
    5: ("fermentation_glucose", "Брожение глюкозы"),
    6: ("neutralization_hcl_naoh", "Нейтрализация"),
}


class RouteCard(ButtonBehavior, BoxLayout):
    def __init__(self, item: RouteItem, on_open=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(130)
        self.padding = [dp(14), dp(12)]
        self.spacing = dp(6)
        self._on_open = on_open

        with self.canvas.before:
            Color(0.12, 0.15, 0.23, 1)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
        self.bind(pos=self._upd, size=self._upd)

        self.add_widget(
            MarqueeLabel(
                text=item.section_title,
                bold=True,
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
                font_size=sp(14),
                size_hint_y=None,
                height=dp(24),
                speed=1.8,
            )
        )
        self.add_widget(
            MDLabel(
                text=f"Ср.результ.: {item.avg_percent:.0f}% | Лучш.: {item.best_percent:.0f}% | Попыт.: {item.attempts}",
                theme_text_color="Custom",
                text_color=(0.75, 0.8, 0.9, 1),
                font_size=sp(11),
                size_hint_y=None,
                height=dp(20),
                shorten=True,
                shorten_from="right",
                max_lines=1,
            )
        )
        self.add_widget(
            MDLabel(
                text=f"Реком. опыт: {item.reaction_title}",
                theme_text_color="Custom",
                text_color=(0.6, 0.9, 0.8, 1),
                font_size=sp(11),
                size_hint_y=None,
                height=dp(20),
                shorten=True,
                shorten_from="right",
                max_lines=1,
            )
        )

        row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(36))

        b1 = MDButton(style="outlined", size_hint_x=0.34)
        b1.add_widget(MDButtonText(text="Теория"))
        b1.bind(on_release=lambda *_: self._on_open("section"))
        row.add_widget(b1)

        b2 = MDButton(style="outlined", size_hint_x=0.33)
        b2.add_widget(MDButtonText(text="Тест"))
        b2.bind(on_release=lambda *_: self._on_open("quiz"))
        row.add_widget(b2)

        b3 = MDButton(style="filled", size_hint_x=0.33)
        b3.add_widget(MDButtonText(text="Опыт"))
        b3.bind(on_release=lambda *_: self._on_open("reaction"))
        row.add_widget(b3)

        self.add_widget(row)

    def _upd(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


class AdaptiveRouteScreen(BaseScreen):
    def on_pre_enter(self, *args):
        self.title = "Учебный маршрут"
        super().on_pre_enter(*args)
        Clock.schedule_once(lambda *_: self._build_ui(), 0)

    def _conn(self) -> sqlite3.Connection:
        app = self.get_app()
        conn = sqlite3.connect(app.courses_db)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_items(self) -> list[RouteItem]:
        rows = []
        with self._conn() as c:
            rows = c.execute(
                """
                SELECT
                    cs.id as section_id,
                    cs.title as section_title,
                    sp.best_percent as best_percent,
                    sp.last_percent as last_percent,
                    sp.attempts_count as attempts,
                    sp.correct_answers as correct_answers,
                    sp.total_answers as total_answers
                FROM mm_section_progress sp
                JOIN course_sections cs ON cs.id = sp.section_id
                ORDER BY (1.0 * sp.correct_answers / CASE WHEN sp.total_answers <= 0 THEN 1 ELSE sp.total_answers END) ASC,
                         sp.attempts_count DESC
                LIMIT 4
                """
            ).fetchall()

            if not rows:
                rows = c.execute(
                    """
                    SELECT
                        cs.id as section_id,
                        cs.title as section_title,
                        COALESCE(MAX(a.percent), 0) as best_percent,
                        COALESCE(AVG(a.percent), 0) as avg_percent,
                        COUNT(a.id) as attempts
                    FROM course_sections cs
                    LEFT JOIN mm_quizzes q ON q.section_id = cs.id
                    LEFT JOIN mm_quiz_attempts a ON a.quiz_id = q.id
                    GROUP BY cs.id, cs.title
                    ORDER BY avg_percent ASC, attempts DESC
                    LIMIT 4
                    """
                ).fetchall()
                out: list[RouteItem] = []
                for r in rows:
                    sid = int(r["section_id"])
                    reaction_id, reaction_title = REACTION_BY_SECTION.get(sid, ("neutralization_hcl_naoh", "Нейтрализация"))
                    out.append(
                        RouteItem(
                            section_id=sid,
                            section_title=str(r["section_title"]),
                            avg_percent=float(r["avg_percent"] or 0),
                            best_percent=float(r["best_percent"] or 0),
                            attempts=int(r["attempts"] or 0),
                            reaction_id=reaction_id,
                            reaction_title=reaction_title,
                        )
                    )
                return out

        out: list[RouteItem] = []
        for r in rows:
            sid = int(r["section_id"])
            reaction_id, reaction_title = REACTION_BY_SECTION.get(sid, ("neutralization_hcl_naoh", "Нейтрализация"))
            total_answers = int(r["total_answers"] or 0)
            correct_answers = int(r["correct_answers"] or 0)
            avg = (100.0 * correct_answers / total_answers) if total_answers > 0 else float(r["last_percent"] or 0)
            out.append(
                RouteItem(
                    section_id=sid,
                    section_title=str(r["section_title"]),
                    avg_percent=float(avg),
                    best_percent=float(r["best_percent"] or 0),
                    attempts=int(r["attempts"] or 0),
                    reaction_id=reaction_id,
                    reaction_title=reaction_title,
                )
            )
        return out

    def _build_ui(self):
        self.clear_widgets()
        app = self.get_app()

        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        with root.canvas.before:
            Color(*app.mm_bg)
            self._bg = RoundedRectangle(pos=root.pos, size=root.size, radius=[0])
        root.bind(pos=lambda *_: setattr(self._bg, "pos", root.pos), size=lambda *_: setattr(self._bg, "size", root.size))

        root.add_widget(
            MDLabel(
                text="Маршрут по слабым местам",
                bold=True,
                halign="center",
                theme_text_color="Custom",
                text_color=app.mm_text,
                font_size=sp(20),
                size_hint_y=None,
                height=dp(34),
            )
        )

        root.add_widget(
            MDLabel(
                text="Порядок: теория -> тест -> связанный опыт",
                halign="center",
                theme_text_color="Custom",
                text_color=app.mm_text2,
                font_size=sp(12),
                size_hint_y=None,
                height=dp(20),
            )
        )

        items = self._load_items()
        if not items:
            root.add_widget(
                MDLabel(
                    text="Пока нет статистики. Пройдите хотя бы один тест, и маршрут появится автоматически.",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=app.mm_text2,
                )
            )
            self.add_widget(root)
            return

        scroll = MDScrollView()
        col = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10), padding=[0, 0, 0, dp(14)])
        col.bind(minimum_height=col.setter("height"))

        for item in items:
            def on_open(action: str, route=item):
                if action == "section":
                    courses = app.course_repo.list_courses()
                    if not courses:
                        return
                    course = courses[0]
                    app.open_course(int(course.id), str(course.title))
                    Clock.schedule_once(lambda *_: app.open_section(route.section_id, route.section_title), 0.05)
                    return
                if action == "quiz":
                    app.nav_state = {
                        "section_id": route.section_id,
                        "section_title": route.section_title,
                        "quiz_return": "adaptive_route",
                    }
                    app.set_top_title("Тест")
                    app._set_screen("quiz")
                    return
                app.open_reaction_viewer(route.reaction_id, route.reaction_title)

            col.add_widget(RouteCard(item=item, on_open=on_open))

        extra_btn = MDButton(style="filled", size_hint=(None, None), size=(dp(260), dp(42)), pos_hint={"center_x": 0.5})
        extra_btn.add_widget(MDButtonText(text="Тренажер ОГЭ/ЕГЭ"))
        extra_btn.bind(on_release=lambda *_: app.open_exam_prep())
        col.add_widget(extra_btn)

        scroll.add_widget(col)
        root.add_widget(scroll)
        self.add_widget(root)
