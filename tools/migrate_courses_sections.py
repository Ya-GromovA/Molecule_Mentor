
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "courses" / "courses.db"


def main() -> int:
    if not DB.exists():
        print(f"[ERROR] DB not found: {DB}")
        return 2

    conn = sqlite3.connect(str(DB))
    try:
        cur = conn.cursor()
        tables = set(r[0] for r in cur.execute("select name from sqlite_master where type='table'").fetchall())
        required = {"courses", "course_sections", "course_topics", "topic_blocks"}
        missing = required - tables
        if missing:
            print(f"[ERROR] Missing tables: {sorted(missing)}")
            return 3

        courses = cur.execute("select count(*) from courses").fetchone()[0]
        sections = cur.execute("select count(*) from course_sections").fetchone()[0]
        topics = cur.execute("select count(*) from course_topics").fetchone()[0]
        blocks = cur.execute("select count(*) from topic_blocks").fetchone()[0]
        print("[OK] Current catalog:")
        print(f"  courses={courses}")
        print(f"  course_sections={sections}")
        print(f"  course_topics={topics}")
        print(f"  topic_blocks={blocks}")

        if topics == 0 or sections == 0:
            print("[WARN] course_sections/course_topics empty — migration/seeding may be needed.")
        else:
            print("[OK] Nothing to migrate for sections/topics (already filled).")

        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
