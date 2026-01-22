from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Optional

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from kivymd.uix.button import MDButton
from kivymd.uix.label import MDLabel
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.list import MDList
from kivymd.uix.scrollview import MDScrollView

from .base_screen import BaseScreen


@dataclass(frozen=True)
class Q:
    q: str
    options: list[str]
    correct: int
    explanation: str


class QuizScreen(BaseScreen):
    def on_pre_enter(self, *args):
        self.title = "Тест"
        super().on_pre_enter(*args)
        Clock.schedule_once(lambda *_: self._load(), 0)

    def _conn(self) -> sqlite3.Connection:
        app = self.get_app()
        conn = sqlite3.connect(app.courses_db)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _load(self):
        app = self.get_app()
        course_id = app.nav_state.get("course_id")
        self.clear_widgets()

        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))

        if course_id is None:
            root.add_widget(MDLabel(text="Не выбран курс для теста", halign="center"))
            self.add_widget(root)
            return

        with self._conn() as c:
            quiz = c.execute(
                "select id, title from mm_quizzes where course_id=? order by id limit 1",
                (int(course_id),),
            ).fetchone()

            if not quiz:
                root.add_widget(MDLabel(text="Тест не найден. Автосид должен был создать тесты.", halign="center"))
                self.add_widget(root)
                return

            quiz_id = int(quiz["id"])
            q_rows = c.execute(
                "select q, options_json, correct_index, explanation from mm_quiz_questions where quiz_id=? order by order_index",
                (quiz_id,),
            ).fetchall()

        self._quiz_id = quiz_id
        self._course_id = int(course_id)

        self._questions: list[Q] = []
        for r in q_rows:
            opts = json.loads(r["options_json"])
            self._questions.append(
                Q(
                    q=str(r["q"]),
                    options=[str(x) for x in opts],
                    correct=int(r["correct_index"]),
                    explanation=str(r["explanation"] or ""),
                )
            )

        if not self._questions:
            root.add_widget(MDLabel(text="В тесте нет вопросов. Автосид должен был добавить вопросы.", halign="center"))
            self.add_widget(root)
            return

        self._answers: dict[int, int] = {}

        scroll = MDScrollView()
        lst = MDList()

        lst.add_widget(MDLabel(
            text=str(quiz["title"]),
            bold=True,
            halign="center",
            adaptive_height=True,
            padding=(dp(16), dp(12)),
            theme_text_color="Custom",
            text_color=app.mm_text,
        ))

        # сохраняем строки чекбоксов по вопросу, чтобы правильно переключать
        self._rows: list[list[MDCheckbox]] = []

        for qidx, q in enumerate(self._questions):
            lst.add_widget(MDLabel(
                text=f"{qidx + 1}. {q.q}",
                adaptive_height=True,
                padding=(dp(16), dp(10)),
                theme_text_color="Custom",
                text_color=app.mm_text,
            ))
            cbs: list[MDCheckbox] = []
            for oidx, opt in enumerate(q.options):
                row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), padding=(dp(16), 0), spacing=dp(10))
                cb = MDCheckbox(active=False)
                lbl = MDLabel(text=opt, halign="left", theme_text_color="Custom", text_color=app.mm_text)

                def pick(_w, _touch=None, qi=qidx, oi=oidx):
                    self._answers[qi] = oi
                    self._refresh_checks()
                    return True

                cb.bind(on_release=pick)
                lbl.bind(on_touch_down=lambda w, t, qi=qidx, oi=oidx: pick(w, t, qi, oi))

                cbs.append(cb)
                row.add_widget(cb)
                row.add_widget(lbl)
                lst.add_widget(row)

            self._rows.append(cbs)

        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56), padding=(dp(16), dp(8)), spacing=dp(12))
        submit = MDButton(text="Завершить", style="filled", on_release=lambda *_: self._submit())
        retry = MDButton(text="Пройти снова", style="outlined", on_release=lambda *_: self._retry())
        btn_row.add_widget(submit)
        btn_row.add_widget(retry)
        lst.add_widget(btn_row)

        self._result_label = MDLabel(
            text="",
            halign="center",
            adaptive_height=True,
            padding=(dp(16), dp(10)),
            theme_text_color="Custom",
            text_color=app.mm_text2,
        )
        lst.add_widget(self._result_label)

        scroll.add_widget(lst)
        root.add_widget(scroll)
        self.add_widget(root)

        self._refresh_checks()

    def _refresh_checks(self):
        for qidx, cbs in enumerate(self._rows):
            chosen = self._answers.get(qidx)
            for oidx, cb in enumerate(cbs):
                cb.active = (chosen == oidx)

    def _retry(self):
        self._answers = {}
        self._refresh_checks()
        self._result_label.text = ""

    def _submit(self):
        if len(self._answers) < len(self._questions):
            self.get_app().toast("Ответь на все вопросы")
            return

        score = 0
        for idx, q in enumerate(self._questions):
            if self._answers.get(idx) == q.correct:
                score += 1

        total = len(self._questions)
        percent = round(score * 100.0 / total, 2)

        with self._conn() as c:
            c.execute(
                "insert into mm_quiz_attempts(quiz_id, finished_at, score, total, percent) "
                "values (?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?, ?, ?)",
                (self._quiz_id, score, total, percent),
            )

            row = c.execute(
                "select best_percent, attempts_count from mm_course_progress where course_id=?",
                (self._course_id,),
            ).fetchone()

            if row:
                best = max(float(row["best_percent"]), percent)
                attempts = int(row["attempts_count"]) + 1
                c.execute(
                    "update mm_course_progress set best_percent=?, last_percent=?, attempts_count=?, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') where course_id=?",
                    (best, percent, attempts, self._course_id),
                )
            else:
                c.execute(
                    "insert into mm_course_progress(course_id, best_percent, last_percent, attempts_count) values (?, ?, ?, ?)",
                    (self._course_id, percent, percent, 1),
                )

            c.commit()

        self._result_label.text = f"Результат: {score}/{total} ({percent:.0f}%)"
        self.get_app().toast("Результат сохранён")
