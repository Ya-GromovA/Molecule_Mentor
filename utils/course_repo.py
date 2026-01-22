from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class Course:
    id: int
    grade: int
    level: str
    title: str


@dataclass(frozen=True)
class CourseSection:
    id: int
    course_id: int
    section_key: str
    title: str
    position: int


@dataclass(frozen=True)
class CourseTopic:
    id: int
    section_id: int
    topic_key: str
    title: str
    position: int


@dataclass(frozen=True)
class TopicBlock:
    id: int
    topic_id: int
    block_type: str  # text|image
    content: str
    caption: Optional[str]
    position: int


class CourseRepo:
    def __init__(self, db_path: str):
        if not os.path.exists(db_path):
            raise FileNotFoundError(db_path)
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # -------- Catalog (courses/sections/topics/blocks) --------
    def list_courses(self) -> list[Course]:
        with self._conn() as c:
            rows = c.execute("select id, grade, level, title from courses order by grade, level").fetchall()
        return [Course(id=r["id"], grade=r["grade"], level=r["level"], title=r["title"]) for r in rows]

    def list_sections(self, course_id: int) -> list[CourseSection]:
        with self._conn() as c:
            rows = c.execute(
                "select id, course_id, section_key, title, position from course_sections where course_id=? order by position",
                (course_id,),
            ).fetchall()
        return [
            CourseSection(
                id=r["id"],
                course_id=r["course_id"],
                section_key=r["section_key"],
                title=r["title"],
                position=r["position"],
            )
            for r in rows
        ]

    def list_topics(self, section_id: int) -> list[CourseTopic]:
        with self._conn() as c:
            rows = c.execute(
                "select id, section_id, topic_key, title, position from course_topics where section_id=? order by position",
                (section_id,),
            ).fetchall()
        return [
            CourseTopic(
                id=r["id"],
                section_id=r["section_id"],
                topic_key=r["topic_key"],
                title=r["title"],
                position=r["position"],
            )
            for r in rows
        ]

    def get_topic(self, topic_id: int) -> Optional[CourseTopic]:
        with self._conn() as c:
            r = c.execute(
                "select id, section_id, topic_key, title, position from course_topics where id=?",
                (topic_id,),
            ).fetchone()
        if not r:
            return None
        return CourseTopic(
            id=r["id"],
            section_id=r["section_id"],
            topic_key=r["topic_key"],
            title=r["title"],
            position=r["position"],
        )

    def list_blocks(self, topic_id: int) -> list[TopicBlock]:
        with self._conn() as c:
            rows = c.execute(
                "select id, topic_id, block_type, content, caption, position from topic_blocks where topic_id=? order by position",
                (topic_id,),
            ).fetchall()
        return [
            TopicBlock(
                id=r["id"],
                topic_id=r["topic_id"],
                block_type=r["block_type"],
                content=r["content"],
                caption=r["caption"],
                position=r["position"],
            )
            for r in rows
        ]

    def get_course_id_for_topic(self, topic_id: int) -> Optional[int]:
        with self._conn() as c:
            r = c.execute(
                """
                select cs.course_id as course_id
                from course_topics ct
                join course_sections cs on cs.id = ct.section_id
                where ct.id = ?
                """,
                (topic_id,),
            ).fetchone()
        if not r:
            return None
        return int(r["course_id"])

    # -------- mm_* (quizzes/progress) safe readers --------
    def has_mm_tables(self) -> bool:
        with self._conn() as c:
            rows = c.execute(
                "select name from sqlite_master where type='table' and name in ('mm_quizzes','mm_quiz_questions','mm_quiz_attempts','mm_course_progress')"
            ).fetchall()
        names = {r["name"] for r in rows}
        return {"mm_quizzes", "mm_quiz_questions", "mm_quiz_attempts", "mm_course_progress"}.issubset(names)

    def get_course_progress(self, course_id: int) -> Tuple[float, float, int]:
        """
        Returns (best_percent, last_percent, attempts_count).
        If mm_course_progress doesn't exist -> (0,0,0).
        """
        with self._conn() as c:
            t = c.execute(
                "select name from sqlite_master where type='table' and name='mm_course_progress'"
            ).fetchone()
            if not t:
                return (0.0, 0.0, 0)

            r = c.execute(
                "select best_percent, last_percent, attempts_count from mm_course_progress where course_id=?",
                (course_id,),
            ).fetchone()
            if not r:
                return (0.0, 0.0, 0)

        return (float(r["best_percent"]), float(r["last_percent"]), int(r["attempts_count"]))
