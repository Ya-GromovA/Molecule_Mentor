
from __future__ import annotations

import sqlite3
from pathlib import Path

DB = Path("/home/ulyashka_88/molecule-mentor/data/courses/courses.db")


def main() -> int:
    if not DB.exists():
        print(f"DB not found: {DB}")
        return 2

    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    try:
        tables = [r["name"] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")]
        print("Tables:", ", ".join(tables) if tables else "(none)")

        def scalar(sql: str) -> int:
            r = con.execute(sql).fetchone()
            return int(list(r)[0]) if r else 0

        print("\nCourses:")
        for r in con.execute("SELECT id, title, grade, level FROM courses ORDER BY grade, level;"):
            print(f" - {r['id']} | grade={r['grade']} level={r['level']} | {r['title']}")

        print("\nCounts:")
        for t in ["sections", "topics", "topic_blocks"]:
            if t in tables:
                print(f" - {t}: {scalar(f'SELECT COUNT(*) FROM {t};')}")
            else:
                print(f" - {t}: table missing")

        print("\nSanity sample topics:")
        if "topics" in tables:
            for r in con.execute("SELECT id, title FROM topics ORDER BY order_index LIMIT 10;"):
                print(f" - {r['id']} | {r['title']}")

        return 0
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
