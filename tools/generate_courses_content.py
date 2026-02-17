
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "courses" / "courses.db"





@dataclass(frozen=True)
class OutlineTopic:
    title: str
    key: str


@dataclass(frozen=True)
class OutlineSection:
    title: str
    key: str
    topics: List[OutlineTopic]


@dataclass(frozen=True)
class CourseOutline:
    course_title: str
    grade: int
    level: str
    sections: List[OutlineSection]





def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^\w\s-]+", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s]+", "-", s, flags=re.UNICODE)
    s = re.sub(r"-{2,}", "-", s)
    return s[:64] if s else "item"


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _require_hf_token() -> str:
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "HF_TOKEN не найден в окружении. Сделай:\n"
            "  export HF_TOKEN=\"$(cat /home/ulyashka_88/molecule-mentor/data/secrets/hf_token.txt)\""
        )
    return token





class CoursesDB:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.db_path))
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON;")
        return con

    def init_schema(self) -> None:
        with self.connect() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grade INTEGER NOT NULL,
                    level TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_courses_grade_level
                ON courses(grade, level);

                CREATE TABLE IF NOT EXISTS course_sections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER NOT NULL,
                    section_key TEXT NOT NULL,
                    title TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    created_at TEXT,
                    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_sections_course_key
                ON course_sections(course_id, section_key);

                CREATE TABLE IF NOT EXISTS course_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    section_id INTEGER NOT NULL,
                    topic_key TEXT NOT NULL,
                    title TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    created_at TEXT,
                    FOREIGN KEY(section_id) REFERENCES course_sections(id) ON DELETE CASCADE
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_topics_section_key
                ON course_topics(section_id, topic_key);

                -- Контент темы — блоки (текст/изображение/формула/список и т.п.)
                CREATE TABLE IF NOT EXISTS topic_blocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic_id INTEGER NOT NULL,
                    block_type TEXT NOT NULL,  -- text | image
                    content TEXT NOT NULL,     -- для image: относительный путь
                    caption TEXT,
                    position INTEGER NOT NULL,
                    created_at TEXT,
                    FOREIGN KEY(topic_id) REFERENCES course_topics(id) ON DELETE CASCADE
                );
                """
            )
            con.commit()


        self._migrate_add_column("courses", "created_at", "TEXT")
        self._migrate_add_column("course_sections", "created_at", "TEXT")
        self._migrate_add_column("course_topics", "created_at", "TEXT")
        self._migrate_add_column("topic_blocks", "created_at", "TEXT")

    def _migrate_add_column(self, table: str, column: str, coltype: str) -> None:
        with self.connect() as con:
            cols = [r["name"] for r in con.execute(f"PRAGMA table_info({table});").fetchall()]
            if column in cols:
                return
            con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype};")
            con.commit()

    def reset_all(self) -> None:
        with self.connect() as con:
            con.executescript(
                """
                DROP TABLE IF EXISTS topic_blocks;
                DROP TABLE IF EXISTS course_topics;
                DROP TABLE IF EXISTS course_sections;
                DROP TABLE IF EXISTS courses;
                """
            )
            con.commit()

    def upsert_course(self, grade: int, level: str, title: str) -> int:
        with self.connect() as con:
            now = _now_iso()
            row = con.execute(
                "SELECT id FROM courses WHERE grade=? AND level=?;",
                (grade, level),
            ).fetchone()
            if row:
                con.execute("UPDATE courses SET title=? WHERE id=?;", (title, int(row["id"])))
                con.commit()
                return int(row["id"])

            con.execute(
                "INSERT INTO courses(grade, level, title, created_at) VALUES (?,?,?,?);",
                (grade, level, title, now),
            )
            con.commit()
            return int(con.execute("SELECT last_insert_rowid();").fetchone()[0])

    def upsert_section(self, course_id: int, section_key: str, title: str, position: int) -> int:
        with self.connect() as con:
            now = _now_iso()
            row = con.execute(
                "SELECT id FROM course_sections WHERE course_id=? AND section_key=?;",
                (course_id, section_key),
            ).fetchone()
            if row:
                con.execute(
                    "UPDATE course_sections SET title=?, position=? WHERE id=?;",
                    (title, position, int(row["id"])),
                )
                con.commit()
                return int(row["id"])

            con.execute(
                """
                INSERT INTO course_sections(course_id, section_key, title, position, created_at)
                VALUES (?,?,?,?,?);
                """,
                (course_id, section_key, title, position, now),
            )
            con.commit()
            return int(con.execute("SELECT last_insert_rowid();").fetchone()[0])

    def upsert_topic(self, section_id: int, topic_key: str, title: str, position: int) -> int:
        with self.connect() as con:
            now = _now_iso()
            row = con.execute(
                "SELECT id FROM course_topics WHERE section_id=? AND topic_key=?;",
                (section_id, topic_key),
            ).fetchone()
            if row:
                con.execute(
                    "UPDATE course_topics SET title=?, position=? WHERE id=?;",
                    (title, position, int(row["id"])),
                )
                con.commit()
                return int(row["id"])

            con.execute(
                """
                INSERT INTO course_topics(section_id, topic_key, title, position, created_at)
                VALUES (?,?,?,?,?);
                """,
                (section_id, topic_key, title, position, now),
            )
            con.commit()
            return int(con.execute("SELECT last_insert_rowid();").fetchone()[0])

    def replace_topic_blocks(self, topic_id: int, blocks: List[Dict[str, Any]]) -> None:
        with self.connect() as con:
            con.execute("DELETE FROM topic_blocks WHERE topic_id=?;", (topic_id,))
            now = _now_iso()
            for i, b in enumerate(blocks, start=1):
                con.execute(
                    """
                    INSERT INTO topic_blocks(topic_id, block_type, content, caption, position, created_at)
                    VALUES (?,?,?,?,?,?);
                    """,
                    (topic_id, b["block_type"], b["content"], b.get("caption"), i, now),
                )
            con.commit()





HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"


def hf_chat(prompt: str, model: str = "Qwen/Qwen2.5-7B-Instruct", temperature: float = 0.4) -> str:
    token = _require_hf_token()

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Ты — опытный учитель химии для 10 класса РФ. Пиши чётко, без воды, без выдумок."},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": 1400,
    }

    r = requests.post(
        HF_ROUTER_URL,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"HF Router error {r.status_code}: {r.text[:800]}")
    data = r.json()
    return data["choices"][0]["message"]["content"]


def generate_topic_theory(topic_title: str, section_title: str, grade: int, level: str) -> str:

    prompt1 = textwrap.dedent(
        f"""
        Сгенерируй теорию по теме: "{topic_title}" (раздел "{section_title}") для {grade} класса.
        Уровень: {"углублённый" if level == "adv" else "базовый"}.
        Требования:
        - Пиши понятным языком ученику.
        - Структура: определение/суть → ключевые понятия → примеры → типичные ошибки → мини-вывод.
        - Если приводишь уравнения реакций, то только если уверен(а) на 100%. Иначе пропусти уравнения.
        - Объём: 1200–2000 знаков.
        Верни чистый текст (без markdown).
        """
    ).strip()

    draft = hf_chat(prompt1, temperature=0.35)


    prompt2 = textwrap.dedent(
        f"""
        Отредактируй текст ниже: убери двусмысленности, исправь возможные смысловые/терминологические ошибки,
        сделай изложение проще и точнее для ученика 10 класса. Не добавляй новых фактов сверх текста, только правь.
        Текст:
        {draft}
        """
    ).strip()

    refined = hf_chat(prompt2, temperature=0.2)


    refined = _strip_unsafe_equations(refined)
    return refined.strip()


def _strip_unsafe_equations(text: str) -> str:


    lines = text.splitlines()
    bad = []
    for ln in lines:
        if "→" in ln or "=>" in ln or "→" in ln or "=" in ln and any(x in ln for x in ["+", "→", "->"]):

            bad.append(ln)
    if not bad:
        return text
    kept = [ln for ln in lines if ln not in bad]

    cleaned = "\n".join(kept)
    cleaned = জানা = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned





def outline_auto_chem10_adv() -> CourseOutline:
    course_title = "Химия 10 класс — углублённый курс (органика + общая химия)"
    grade = 10
    level = "adv"


    sections: List[OutlineSection] = [
        OutlineSection(
            title="Введение в органическую химию",
            key="org_intro",
            topics=[
                OutlineTopic("Предмет органической химии. Органические вещества вокруг нас", "org_subject"),
                OutlineTopic("Строение атома углерода. Валентность и гибридизация (sp3, sp2, sp)", "hybridization"),
                OutlineTopic("Химическая связь в органических соединениях: σ- и π-связи", "sigma_pi"),
                OutlineTopic("Изомерия: структурная и пространственная (цис-транс)", "isomerism"),
                OutlineTopic("Классификация органических соединений и номенклатура (ИЮПАК — основы)", "iupac_basics"),
            ],
        ),
        OutlineSection(
            title="Углеводороды",
            key="hydrocarbons",
            topics=[
                OutlineTopic("Алканы: строение, номенклатура, свойства, получение", "alkanes"),
                OutlineTopic("Циклоалканы: особенности строения и свойства", "cycloalkanes"),
                OutlineTopic("Алкены: двойная связь, реакции присоединения, получение", "alkenes"),
                OutlineTopic("Алкадиены. Полимеризация. Каучук и резина", "alkadienes_polymer"),
                OutlineTopic("Алкины: тройная связь, свойства, получение", "alkynes"),
                OutlineTopic("Ароматические углеводороды: бензол, ароматичность, реакции замещения", "arenes"),
            ],
        ),
        OutlineSection(
            title="Кислородсодержащие органические соединения",
            key="oxygen_org",
            topics=[
                OutlineTopic("Спирты: классификация, свойства, получение. Этанол", "alcohols"),
                OutlineTopic("Фенолы: свойства и качественная реакция", "phenols"),
                OutlineTopic("Альдегиды и кетоны: карбонильная группа, свойства", "carbonyls"),
                OutlineTopic("Карбоновые кислоты: кислотность, свойства, получение", "carboxylic_acids"),
                OutlineTopic("Сложные эфиры: этерификация и гидролиз", "esters"),
                OutlineTopic("Жиры: строение, свойства, омыление", "fats"),
            ],
        ),
        OutlineSection(
            title="Азотсодержащие органические соединения",
            key="nitrogen_org",
            topics=[
                OutlineTopic("Амины: строение, основные свойства, получение", "amines"),
                OutlineTopic("Аминокислоты: амфотерность, пептидная связь", "amino_acids"),
                OutlineTopic("Белки: уровни структуры и свойства (денатурация)", "proteins"),
            ],
        ),
        OutlineSection(
            title="Углеводы и биомолекулы",
            key="biomolecules",
            topics=[
                OutlineTopic("Углеводы: моносахариды, дисахариды, полисахариды", "carbohydrates"),
                OutlineTopic("Глюкоза: свойства и качественные реакции", "glucose"),
                OutlineTopic("Полимеры: пластмассы, волокна, основные понятия", "polymers"),
            ],
        ),
        OutlineSection(
            title="Общая химия (повторение и углубление)",
            key="general_chem",
            topics=[
                OutlineTopic("Растворы: концентрации (массовая доля, молярность), расчёты", "solutions"),
                OutlineTopic("Окислительно-восстановительные реакции: степени окисления, баланс", "redox"),
                OutlineTopic("Химическое равновесие и принцип Ле Шателье", "equilibrium"),
                OutlineTopic("Скорость реакции и факторы. Катализ", "kinetics"),
            ],
        ),
    ]
    return CourseOutline(course_title=course_title, grade=grade, level=level, sections=sections)


def outline_to_json(outline: CourseOutline) -> Dict[str, Any]:
    return {
        "course_title": outline.course_title,
        "grade": outline.grade,
        "level": outline.level,
        "sections": [
            {
                "title": s.title,
                "key": s.key,
                "topics": [{"title": t.title, "key": t.key} for t in s.topics],
            }
            for s in outline.sections
        ],
    }


def json_to_outline(data: Dict[str, Any]) -> CourseOutline:
    sections: List[OutlineSection] = []
    for s in data["sections"]:
        topics = [OutlineTopic(title=t["title"], key=t["key"]) for t in s["topics"]]
        sections.append(OutlineSection(title=s["title"], key=s["key"], topics=topics))
    return CourseOutline(
        course_title=data["course_title"],
        grade=int(data["grade"]),
        level=str(data["level"]),
        sections=sections,
    )





def cmd_init_db(args: argparse.Namespace) -> int:
    db = CoursesDB(DB_PATH)
    if args.reset:
        db.reset_all()
    db.init_schema()
    print(f"OK: DB готова: {DB_PATH}")
    return 0


def cmd_outline_auto(args: argparse.Namespace) -> int:
    if args.grade != 10 or args.level != "adv":
        raise RuntimeError("Сейчас outline-auto поддерживает только grade=10 level=adv (для MVP).")

    outline = outline_auto_chem10_adv()
    out_path = Path(args.outline).resolve()
    _write_json(out_path, outline_to_json(outline))
    print(f"OK: outline создан: {out_path}")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    db = CoursesDB(DB_PATH)
    db.init_schema()

    outline_path = Path(args.outline).resolve()
    data = _read_json(outline_path)
    outline = json_to_outline(data)

    if args.reset:


        db.reset_all()
        db.init_schema()

    course_id = db.upsert_course(outline.grade, outline.level, outline.course_title)

    for sec_pos, sec in enumerate(outline.sections, start=1):
        sec_id = db.upsert_section(course_id, sec.key, sec.title, sec_pos)
        for top_pos, top in enumerate(sec.topics, start=1):
            top_id = db.upsert_topic(sec_id, top.key, top.title, top_pos)

            if args.no_ai:
                blocks = [{"block_type": "text", "content": f"Тема: {top.title}\n(пока без генерации текста)", "caption": None}]
            else:
                theory = generate_topic_theory(top.title, sec.title, outline.grade, outline.level)
                blocks = [{"block_type": "text", "content": theory, "caption": None}]

            db.replace_topic_blocks(top_id, blocks)
            print(f"OK: {sec.title} → {top.title}")

    assets_dir = BASE_DIR / "data" / "assets" / "courses" / f"chem10_{outline.level}"
    assets_dir.mkdir(parents=True, exist_ok=True)
    print(f"OK: Курс собран в DB: {DB_PATH}")
    print(f"Assets (папка под иллюстрации): {assets_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="generate_courses_content.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init-db", help="Создать/проверить схему БД (+ миграции)")
    p_init.add_argument("--reset", action="store_true", help="Снести таблицы и создать заново")
    p_init.set_defaults(func=cmd_init_db)

    p_out = sub.add_parser("outline-auto", help="Сгенерировать оглавление курса автоматически (MVP)")
    p_out.add_argument("--outline", required=True, help="Куда сохранить outline.json")
    p_out.add_argument("--grade", type=int, required=True)
    p_out.add_argument("--level", type=str, required=True, choices=["base", "adv"])
    p_out.set_defaults(func=cmd_outline_auto)

    p_build = sub.add_parser("build", help="Собрать пакет курса в SQLite по outline")
    p_build.add_argument("--outline", required=True, help="Путь к outline.json")
    p_build.add_argument("--reset", action="store_true", help="Снести БД и собрать заново")
    p_build.add_argument("--no-ai", action="store_true", help="Не генерировать теорию (только структура)")
    p_build.set_defaults(func=cmd_build)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
