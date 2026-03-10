from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout

from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField

from .base_screen import BaseScreen


@dataclass(frozen=True)
class VirtualLab:
    lab_id: str
    title: str
    reaction_id: str
    reaction_title: str
    objective: str
    steps: str


LABS: list[VirtualLab] = [
    VirtualLab(
        lab_id="lab_neutralization",
        title="ЛР-1. Нейтрализация кислоты и щелочи",
        reaction_id="neutralization_hcl_naoh",
        reaction_title="Нейтрализация: HCl + NaOH",
        objective="Понять признаки нейтрализации и записать итог уравнения.",
        steps="1) Запустите анимацию\n2) Зафиксируйте реагенты и продукты\n3) Сформулируйте вывод",
    ),
    VirtualLab(
        lab_id="lab_ester",
        title="ЛР-2. Этерификация",
        reaction_id="esterification_acetic_ethanol",
        reaction_title="Этерификация: уксусная кислота + этанол",
        objective="Разобрать условия образования сложного эфира и роль реакции.",
        steps="1) Просмотрите ход реакции\n2) Опишите условия процесса\n3) Запишите вывод",
    ),
    VirtualLab(
        lab_id="lab_precipitation",
        title="ЛР-3. Реакция осаждения",
        reaction_id="precipitation_agcl",
        reaction_title="Осаждение AgCl",
        objective="Определить признак реакции и объяснить образование осадка.",
        steps="1) Запустите опыт\n2) Отметьте признак реакции\n3) Сделайте вывод",
    ),
    VirtualLab(
        lab_id="lab_redox",
        title="ЛР-4. Реакция замещения",
        reaction_id="zn_cu_displacement",
        reaction_title="Замещение: Zn вытесняет Cu",
        objective="Понять, как идет окислительно-восстановительный процесс.",
        steps="1) Просмотрите анимацию\n2) Опишите изменение веществ\n3) Сформулируйте вывод",
    ),
]


class VirtualLabsScreen(BaseScreen):
    def on_pre_enter(self, *args):
        self.title = "Виртуальные лабораторные"
        super().on_pre_enter(*args)
        Clock.schedule_once(lambda *_: self._build_ui(), 0)

    def _conn(self) -> sqlite3.Connection:
        app = self.get_app()
        conn = sqlite3.connect(app.courses_db)
        conn.row_factory = sqlite3.Row
        return conn

    def _recent_reports_count(self) -> int:
        with self._conn() as c:
            row = c.execute("SELECT COUNT(*) as c FROM mm_lab_reports").fetchone()
            return int(row["c"] or 0)

    def _save_report(self, lab: VirtualLab, hypothesis: str, observations: str, conclusion: str) -> int:
        score = 0
        if len((hypothesis or "").strip()) >= 20:
            score += 1
        if len((observations or "").strip()) >= 30:
            score += 1
        if len((conclusion or "").strip()) >= 20:
            score += 1
        with self._conn() as c:
            c.execute(
                """
                INSERT INTO mm_lab_reports(lab_id, reaction_id, title, hypothesis, observations, conclusion, score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lab.lab_id,
                    lab.reaction_id,
                    lab.title,
                    (hypothesis or "").strip(),
                    (observations or "").strip(),
                    (conclusion or "").strip(),
                    score,
                ),
            )
            c.commit()
        return score

    def _build_lab_card(self, lab: VirtualLab) -> BoxLayout:
        app = self.get_app()
        card = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=[dp(12), dp(12)])
        card.bind(minimum_height=card.setter("height"))

        with card.canvas.before:
            Color(0.12, 0.15, 0.22, 1)
            bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(14)])
        card.bind(pos=lambda *_: setattr(bg, "pos", card.pos), size=lambda *_: setattr(bg, "size", card.size))

        card.add_widget(
            MDLabel(
                text=lab.title,
                bold=True,
                theme_text_color="Custom",
                text_color=app.mm_text,
                font_size=sp(15),
                size_hint_y=None,
                height=dp(24),
            )
        )
        card.add_widget(
            MDLabel(
                text=f"Цель: {lab.objective}",
                theme_text_color="Custom",
                text_color=app.mm_text2,
                font_size=sp(12),
                size_hint_y=None,
                height=dp(40),
            )
        )
        card.add_widget(
            MDLabel(
                text=f"Протокол: {lab.steps}",
                theme_text_color="Custom",
                text_color=(0.7, 0.9, 0.85, 1),
                font_size=sp(12),
                size_hint_y=None,
                height=dp(54),
            )
        )

        hypothesis = MDTextField(hint_text="Гипотеза", mode="filled", multiline=True, size_hint_y=None, height=dp(68))
        observations = MDTextField(hint_text="Наблюдения", mode="filled", multiline=True, size_hint_y=None, height=dp(84))
        conclusion = MDTextField(hint_text="Вывод", mode="filled", multiline=True, size_hint_y=None, height=dp(68))

        card.add_widget(hypothesis)
        card.add_widget(observations)
        card.add_widget(conclusion)

        row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(40))

        open_btn = MDButton(style="outlined", size_hint_x=0.42)
        open_btn.add_widget(MDButtonText(text="Показать опыт"))
        open_btn.bind(on_release=lambda *_: app.open_reaction_viewer(lab.reaction_id, lab.reaction_title))
        row.add_widget(open_btn)

        save_btn = MDButton(style="filled", size_hint_x=0.58)
        save_btn.add_widget(MDButtonText(text="Сохранить протокол"))

        def on_save(*_):
            score = self._save_report(lab, hypothesis.text, observations.text, conclusion.text)
            app.toast(f"Протокол сохранен. Заполненность: {score}/3")

        save_btn.bind(on_release=on_save)
        row.add_widget(save_btn)

        card.add_widget(row)
        return card

    def _build_ui(self):
        self.clear_widgets()
        app = self.get_app()

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        with root.canvas.before:
            Color(*app.mm_bg)
            self._bg = RoundedRectangle(pos=root.pos, size=root.size, radius=[0])
        root.bind(pos=lambda *_: setattr(self._bg, "pos", root.pos), size=lambda *_: setattr(self._bg, "size", root.size))

        root.add_widget(
            MDLabel(
                text="Виртуальные лабораторные работы",
                bold=True,
                halign="center",
                theme_text_color="Custom",
                text_color=app.mm_text,
                font_size=sp(20),
                size_hint_y=None,
                height=dp(34),
            )
        )

        reports_count = self._recent_reports_count()
        root.add_widget(
            MDLabel(
                text=f"Сохраненных протоколов: {reports_count}",
                halign="center",
                theme_text_color="Custom",
                text_color=app.mm_text2,
                font_size=sp(12),
                size_hint_y=None,
                height=dp(20),
            )
        )

        scroll = MDScrollView()
        col = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None, padding=[0, 0, 0, dp(20)])
        col.bind(minimum_height=col.setter("height"))

        for lab in LABS:
            col.add_widget(self._build_lab_card(lab))

        scroll.add_widget(col)
        root.add_widget(scroll)
        self.add_widget(root)
