
from __future__ import annotations

import json
import sqlite3
from pathlib import Path


DB = Path("/home/ulyashka_88/molecule-mentor/data/courses/courses.db")


QUESTIONS = [
    {
        "q": "Что изучает органическая химия?",
        "options": [
            "Только неорганические соли",
            "Соединения углерода и их превращения",
            "Только металлы и их сплавы",
            "Только кислотно-основные реакции",
        ],
        "correct": 1,
        "explanation": "Органическая химия изучает соединения углерода (за редкими исключениями) и их реакции."
    },
    {
        "q": "Гибридизация sp2 у углерода соответствует геометрии:",
        "options": ["Тетраэдрической", "Тригонально-плоской", "Линейной", "Октаэдрической"],
        "correct": 1,
        "explanation": "sp2 → тригонально-плоская геометрия, угол ~120°."
    },
    {
        "q": "σ-связь образуется при перекрывании орбиталей преимущественно:",
        "options": ["Боковом", "Лобовом", "Только d-орбиталей", "Только p-орбиталей"],
        "correct": 1,
        "explanation": "σ — лобовое (осевое) перекрывание."
    },
    {
        "q": "Какой класс относится к углеводородам?",
        "options": ["Спирты", "Алканы", "Карбоновые кислоты", "Амины"],
        "correct": 1,
        "explanation": "Алканы — углеводороды (только C и H)."
    },
    {
        "q": "Качественная реакция на фенолы в школьном курсе чаще всего:",
        "options": ["Серебряное зеркало", "FeCl3 (фиолетовое окрашивание)", "Бромная вода (обесцвечивание)", "KMnO4 (обесцвечивание)"],
        "correct": 1,
        "explanation": "FeCl3 даёт характерное окрашивание с фенолами."
    },
    {
        "q": "Этерификация — это реакция образования:",
        "options": ["Амида", "Сложного эфира", "Альдегида", "Алкана"],
        "correct": 1,
        "explanation": "Этерификация: кислота + спирт → сложный эфир + вода."
    },
    {
        "q": "Принцип Ле Шателье описывает:",
        "options": ["Скорость реакции", "Смещение равновесия при изменении условий", "Только кислотность растворов", "Степени окисления"],
        "correct": 1,
        "explanation": "Равновесие смещается так, чтобы ослабить внешнее воздействие."
    },
]


def main() -> int:
    if not DB.exists():
        print(f"[ERROR] DB not found: {DB}")
        return 2

    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()


        cur.execute("select name from sqlite_master where type='table' and name='mm_quizzes'")
        if not cur.fetchone():
            print("[ERROR] mm_quizzes not found. Run migrate_quizzes_and_progress.py first.")
            return 3

        course = cur.execute("select id, title from courses order by id limit 1").fetchone()
        if not course:
            print("[ERROR] No courses found.")
            return 4

        course_id = int(course["id"])
        existing = cur.execute("select count(*) as c from mm_quizzes where course_id=?", (course_id,)).fetchone()["c"]
        if existing > 0:
            print(f"[OK] Quizzes already seeded for course_id={course_id}. Skipping.")
            return 0

        quiz_title = "Тест по курсу (основы органики + общая химия)"
        cur.execute(
            "insert into mm_quizzes(course_id, title) values (?, ?)",
            (course_id, quiz_title),
        )
        quiz_id = cur.lastrowid

        for idx, q in enumerate(QUESTIONS, start=1):
            cur.execute(
                """
                insert into mm_quiz_questions(quiz_id, q, options_json, correct_index, explanation, order_index)
                values (?, ?, ?, ?, ?, ?)
                """,
                (
                    quiz_id,
                    q["q"],
                    json.dumps(q["options"], ensure_ascii=False),
                    int(q["correct"]),
                    q.get("explanation", ""),
                    idx,
                ),
            )

        conn.commit()
        print(f"[OK] Seeded quiz_id={quiz_id} ({len(QUESTIONS)} questions) for course_id={course_id}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
