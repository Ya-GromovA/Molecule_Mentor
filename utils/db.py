
from __future__ import annotations

import sqlite3
from pathlib import Path


def get_db_path(base_dir: Path) -> Path:
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "app.sqlite3"


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )


    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            status TEXT NOT NULL,
            progress_value REAL NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, entity_type, entity_id)
        );
        """
    )


    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            quiz_id TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )


    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            session_key TEXT NOT NULL UNIQUE,
            title TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )






    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS courses (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            grade INTEGER NOT NULL,
            level TEXT NOT NULL,
            hours_per_year INTEGER NOT NULL,
            source_name TEXT,
            source_url TEXT,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )


    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS course_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            section_id TEXT NOT NULL,
            title TEXT NOT NULL,
            order_index INTEGER NOT NULL DEFAULT 0,
            UNIQUE(course_id, section_id)
        );
        """
    )


    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS course_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_pk INTEGER NOT NULL REFERENCES course_sections(id) ON DELETE CASCADE,
            topic_id TEXT,
            title TEXT NOT NULL,
            order_index INTEGER NOT NULL DEFAULT 0,
            summary TEXT,
            UNIQUE(section_pk, title)
        );
        """
    )


    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS topic_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_pk INTEGER NOT NULL REFERENCES course_topics(id) ON DELETE CASCADE,
            block_type TEXT NOT NULL,           -- 'text'|'image'|'formula'|'list'
            content TEXT,                       -- markdown/text or image path etc
            caption TEXT,
            order_index INTEGER NOT NULL DEFAULT 0
        );
        """
    )


    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS topic_quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_pk INTEGER NOT NULL REFERENCES course_topics(id) ON DELETE CASCADE,
            question TEXT NOT NULL,
            options_json TEXT NOT NULL,
            correct_index INTEGER NOT NULL,
            explanation TEXT,
            order_index INTEGER NOT NULL DEFAULT 0
        );
        """
    )

    conn.commit()


def ensure_default_user(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT id FROM users ORDER BY id LIMIT 1;").fetchone()
    if row:
        return int(row["id"])
    conn.execute("INSERT INTO users(name) VALUES (?);", ("Default",))
    conn.commit()
    return int(conn.execute("SELECT id FROM users ORDER BY id LIMIT 1;").fetchone()["id"])
