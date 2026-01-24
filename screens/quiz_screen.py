from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Optional

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout

from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList
from kivymd.uix.scrollview import MDScrollView

from .base_screen import BaseScreen


@dataclass(frozen=True)
class Q:
    q: str
    options: list[str]
    correct: int
    explanation: str


class OptionRow(ButtonBehavior, BoxLayout):
    """Кликабельная строка с вариантом ответа."""

    def __init__(self, text: str, selected: bool = False, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(48)
        self.padding = [dp(16), dp(4), dp(16), dp(4)]
        self.spacing = dp(12)
        
        self._selected = selected
        self._on_select = on_select
        self._text = text
        self._indicator_bindeed = False
        self._review_state: Optional[str] = None  # None, "correct", "wrong", "missed"
        self._disabled = False
        
        # Цвета
        self._bg_normal = (0.12, 0.14, 0.22, 1)
        self._bg_selected = (0.2, 0.35, 0.5, 1)
        self._bg_correct = (0.15, 0.45, 0.25, 1)  # зелёный
        self._bg_wrong = (0.5, 0.15, 0.15, 1)  # красный
        self._bg_missed = (0.25, 0.4, 0.25, 1)  # светло-зелёный (правильный, но не выбран)
        
        with self.canvas.before:
            Color(*self._bg_normal)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
        
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # Кружок-индикатор (radio button style)
        self._indicator = BoxLayout(size_hint=(None, None), size=(dp(24), dp(24)))
        self._indicator.pos_hint = {"center_y": 0.5}
        
        # Текст
        self._label = MDLabel(
            text=text,
            halign="left",
            valign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        )
        
        self.add_widget(self._indicator)
        self.add_widget(self._label)
        
        # Биндим позицию индикатора один раз
        self._indicator.bind(pos=self._on_indicator_layout, size=self._on_indicator_layout)
        
        self._update_visuals()

    def _update_rect(self, *_):
        if hasattr(self, '_bg_rect'):
            self._bg_rect.pos = self.pos
            self._bg_rect.size = self.size

    def _on_indicator_layout(self, *_):
        """Перерисовываем индикатор при изменении позиции/размера."""
        self._draw_indicator()

    def _draw_indicator(self):
        """Рисуем кружок-индикатор."""
        self._indicator.canvas.clear()
        with self._indicator.canvas:
            if self._selected:
                # Внешний круг (синий)
                Color(0.3, 0.6, 0.9, 1)
                RoundedRectangle(pos=self._indicator.pos, size=self._indicator.size, radius=[dp(12)])
                # Внутренний круг (белый)
                Color(1, 1, 1, 1)
                inner_size = (dp(10), dp(10))
                inner_pos = (
                    self._indicator.pos[0] + (self._indicator.size[0] - inner_size[0]) / 2,
                    self._indicator.pos[1] + (self._indicator.size[1] - inner_size[1]) / 2,
                )
                RoundedRectangle(pos=inner_pos, size=inner_size, radius=[dp(5)])
            else:
                # Пустой круг (серая обводка)
                Color(0.5, 0.55, 0.65, 1)
                RoundedRectangle(pos=self._indicator.pos, size=self._indicator.size, radius=[dp(12)])
                # Внутренняя часть (цвет фона)
                Color(*self._bg_normal)
                inner_size = (dp(20), dp(20))
                inner_pos = (
                    self._indicator.pos[0] + dp(2),
                    self._indicator.pos[1] + dp(2),
                )
                RoundedRectangle(pos=inner_pos, size=inner_size, radius=[dp(10)])

    def _update_visuals(self):
        """Обновляем цвет фона и индикатор."""
        self.canvas.before.clear()
        with self.canvas.before:
            # Определяем цвет фона
            if self._review_state == "correct":
                Color(*self._bg_correct)
            elif self._review_state == "wrong":
                Color(*self._bg_wrong)
            elif self._review_state == "missed":
                Color(*self._bg_missed)
            elif self._selected:
                Color(*self._bg_selected)
            else:
                Color(*self._bg_normal)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
        self._draw_indicator()

    def set_selected(self, selected: bool):
        if self._selected != selected:
            self._selected = selected
            self._update_visuals()
    
    def set_review_state(self, state: Optional[str]):
        """Устанавливает состояние проверки: 'correct', 'wrong', 'missed' или None."""
        self._review_state = state
        self._update_visuals()
    
    def set_clickable(self, clickable: bool):
        """Включает/отключает возможность выбора."""
        self._disabled = not clickable

    def on_release(self):
        if self._on_select and not self._disabled:
            self._on_select()


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
        self._submitted: bool = False

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

        # сохраняем строки вариантов по вопросу, чтобы правильно переключать
        self._rows: list[list[OptionRow]] = []
        # лейблы для пояснений (показываются после проверки)
        self._explanation_labels: list[MDLabel] = []

        for qidx, q in enumerate(self._questions):
            lst.add_widget(MDLabel(
                text=f"{qidx + 1}. {q.q}",
                adaptive_height=True,
                padding=(dp(16), dp(10)),
                theme_text_color="Custom",
                text_color=app.mm_text,
            ))
            options: list[OptionRow] = []
            for oidx, opt in enumerate(q.options):
                def make_pick(qi, oi):
                    def pick():
                        self._answers[qi] = oi
                        self._refresh_checks()
                    return pick

                option_row = OptionRow(
                    text=opt,
                    selected=False,
                    on_select=make_pick(qidx, oidx),
                )
                options.append(option_row)
                lst.add_widget(option_row)

            self._rows.append(options)
            
            # Лейбл для пояснения (скрыт по умолчанию)
            explanation_label = MDLabel(
                text="",
                adaptive_height=True,
                padding=(dp(16), dp(4), dp(16), dp(12)),
                theme_text_color="Custom",
                text_color=(0.7, 0.8, 0.7, 1),  # светло-зелёный
                size_hint_y=None,
                height=0,
                opacity=0,
            )
            self._explanation_labels.append(explanation_label)
            lst.add_widget(explanation_label)

        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56), padding=(dp(16), dp(8)), spacing=dp(12))
        
        submit = MDButton(style="filled", on_release=lambda *_: self._submit())
        submit.add_widget(MDButtonText(text="Завершить"))
        
        retry = MDButton(style="outlined", on_release=lambda *_: self._retry())
        retry.add_widget(MDButtonText(text="Пройти снова"))
        
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
        for qidx, options in enumerate(self._rows):
            chosen = self._answers.get(qidx)
            for oidx, opt_row in enumerate(options):
                opt_row.set_selected(chosen == oidx)

    def _retry(self):
        self._answers = {}
        self._refresh_checks()
        self._result_label.text = ""
        self._submitted = False
        
        # Сбрасываем состояние проверки и включаем выбор
        for options in self._rows:
            for opt_row in options:
                opt_row.set_review_state(None)
                opt_row.set_clickable(True)
        
        # Скрываем пояснения
        for lbl in self._explanation_labels:
            lbl.text = ""
            lbl.height = 0
            lbl.opacity = 0

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
        
        # Показываем правильные/неправильные ответы
        self._show_review()
    
    def _show_review(self):
        """Показывает результаты: правильные/неправильные ответы и пояснения."""
        self._submitted = True
        
        for qidx, q in enumerate(self._questions):
            chosen = self._answers.get(qidx)
            correct_idx = q.correct
            options = self._rows[qidx]
            
            for oidx, opt_row in enumerate(options):
                # Отключаем возможность менять ответы
                opt_row.set_clickable(False)
                
                if oidx == chosen and oidx == correct_idx:
                    # Выбран правильный ответ
                    opt_row.set_review_state("correct")
                elif oidx == chosen and oidx != correct_idx:
                    # Выбран неправильный ответ
                    opt_row.set_review_state("wrong")
                elif oidx == correct_idx:
                    # Правильный ответ, но не был выбран
                    opt_row.set_review_state("missed")
                else:
                    # Обычный невыбранный вариант
                    opt_row.set_review_state(None)
            
            # Показываем пояснение
            explanation_lbl = self._explanation_labels[qidx]
            is_correct = (chosen == correct_idx)
            
            if is_correct:
                prefix = "Верно!"
                color = (0.5, 0.85, 0.5, 1)  # зелёный
            else:
                prefix = f"Неверно. Правильный ответ: {q.options[correct_idx]}"
                color = (0.95, 0.6, 0.5, 1)  # красноватый
            
            explanation_text = f"{prefix}"
            if q.explanation:
                explanation_text += f"\n{q.explanation}"
            
            explanation_lbl.text = explanation_text
            explanation_lbl.text_color = color
            explanation_lbl.opacity = 1
            # Динамическая высота
            explanation_lbl.texture_update()
            explanation_lbl.height = explanation_lbl.texture_size[1] + dp(16)
