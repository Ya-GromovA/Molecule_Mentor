#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from pathlib import Path


DB = Path("/home/ulyashka_88/molecule-mentor/data/courses/courses.db")


def ensure_tables(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS mm_quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        section_id INTEGER,
        topic_id INTEGER,
        title TEXT NOT NULL,
        created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
        FOREIGN KEY(section_id) REFERENCES course_sections(id) ON DELETE SET NULL,
        FOREIGN KEY(topic_id) REFERENCES course_topics(id) ON DELETE SET NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS mm_quiz_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER NOT NULL,
        q TEXT NOT NULL,
        options_json TEXT NOT NULL,
        correct_index INTEGER NOT NULL,
        explanation TEXT,
        order_index INTEGER NOT NULL,
        FOREIGN KEY(quiz_id) REFERENCES mm_quizzes(id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS mm_quiz_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER NOT NULL,
        started_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        finished_at TEXT,
        score INTEGER NOT NULL,
        total INTEGER NOT NULL,
        percent REAL NOT NULL,
        FOREIGN KEY(quiz_id) REFERENCES mm_quizzes(id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS mm_course_progress (
        course_id INTEGER PRIMARY KEY,
        best_percent REAL NOT NULL DEFAULT 0,
        last_percent REAL NOT NULL DEFAULT 0,
        attempts_count INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
    );
    """)

    conn.commit()


def main() -> int:
    if not DB.exists():
        print(f"[ERROR] DB not found: {DB}")
        return 2

    conn = sqlite3.connect(str(DB))
    try:
        ensure_tables(conn)
        cur = conn.cursor()
        tables = [r[0] for r in cur.execute("select name from sqlite_master where type='table' and name like 'mm_%'").fetchall()]
        print("[OK] Ensured tables:", ", ".join(tables))
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
