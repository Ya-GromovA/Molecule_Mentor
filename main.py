from __future__ import annotations





import os
import sys

def _get_early_log_path() -> str:
    """Получаем путь для раннего лога."""
    android_private = os.environ.get("ANDROID_PRIVATE")
    if android_private:
        return os.path.join(android_private, "early_boot.log")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "early_boot.log")

def _early_log(msg: str) -> None:
    """Пишем в ранний лог."""
    try:
        with open(_get_early_log_path(), "a", encoding="utf-8") as f:
            f.write(f"{msg}\n")
    except Exception:
        pass


_early_log(f"=== PYTHON STARTED ===")
_early_log(f"Python version: {sys.version}")
_early_log(f"ANDROID_PRIVATE: {os.environ.get('ANDROID_PRIVATE', 'NOT SET')}")
_early_log(f"ANDROID_ARGUMENT: {os.environ.get('ANDROID_ARGUMENT', 'NOT SET')}")
_early_log(f"cwd: {os.getcwd()}")
_early_log(f"__file__: {__file__}")




import ctypes
import traceback

_early_log("Imported: ctypes, traceback")

def _is_android() -> bool:
    """Проверка - запущено на телефоне или на компе"""
    return 'ANDROID_ARGUMENT' in os.environ or 'ANDROID_PRIVATE' in os.environ


def _find_system_native_libs() -> str:
    """
    Ищет нативные библиотеки в системных директориях Android.
    Библиотеки, добавленные через android.add_libs_arm64_v8a в buildozer.spec,
    будут находиться в /data/app/.../lib/arm64/ или подобных директориях.
    Возвращает путь к директории с библиотеками или пустую строку.
    """
    _early_log("_find_system_native_libs: searching...")



    potential_paths = []


    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        if activity:
            app_info = activity.getApplicationInfo()
            native_lib_dir = app_info.nativeLibraryDir
            if native_lib_dir:
                potential_paths.append(native_lib_dir)
                _early_log(f"_find_system_native_libs: nativeLibraryDir={native_lib_dir}")
    except Exception as e:
        _early_log(f"_find_system_native_libs: failed to get nativeLibraryDir via jnius: {e}")


    android_private = os.environ.get("ANDROID_PRIVATE", "")
    if android_private:

        data_dir = os.path.dirname(os.path.dirname(android_private))
        potential_paths.extend([
            os.path.join(data_dir, "lib"),
            os.path.join(data_dir, "lib", "arm64"),
            os.path.join(data_dir, "lib", "arm64-v8a"),
        ])



        try:
            data_app = "/data/app"
            if os.path.isdir(data_app):
                for entry in os.listdir(data_app):
                    app_dir = os.path.join(data_app, entry)
                    if os.path.isdir(app_dir):
                        for sub in os.listdir(app_dir):
                            if "moleculementor" in sub.lower() or "molecule" in sub.lower():
                                lib_arm64 = os.path.join(app_dir, sub, "lib", "arm64")
                                lib_arm64_v8a = os.path.join(app_dir, sub, "lib", "arm64-v8a")
                                potential_paths.extend([lib_arm64, lib_arm64_v8a])
                                _early_log(f"_find_system_native_libs: found app dir candidates: {lib_arm64}, {lib_arm64_v8a}")
        except Exception as e:
            _early_log(f"_find_system_native_libs: /data/app scan failed: {e}")


    ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    _early_log(f"_find_system_native_libs: LD_LIBRARY_PATH={ld_path}")
    if ld_path:
        potential_paths.extend(ld_path.split(":"))


    for path in potential_paths:
        if not path or not os.path.isdir(path):
            continue
        lib_path = os.path.join(path, "libllama.so")
        _early_log(f"_find_system_native_libs: checking {lib_path}...")
        if os.path.exists(lib_path):
            _early_log(f"_find_system_native_libs: FOUND at {path}")
            return path

    _early_log("_find_system_native_libs: NOT FOUND in system paths")
    return ""


def _extract_native_libs_android() -> str:
    """
    Извлекает .so файлы из assets/llama в директорию files/native_libs,
    откуда их можно загрузить через dlopen на Android.
    Это fallback на случай если библиотеки не были добавлены через android.add_libs.
    Возвращает путь к директории с библиотеками.
    """
    _early_log("_extract_native_libs: starting...")

    android_private = os.environ.get("ANDROID_PRIVATE", "")
    _early_log(f"_extract_native_libs: ANDROID_PRIVATE={android_private}")

    if not android_private:
        _early_log("_extract_native_libs: ANDROID_PRIVATE not set, aborting")
        return ""


    project_dir = os.path.dirname(os.path.abspath(__file__))
    src_llama_dir = os.path.join(project_dir, "assets", "llama")




    files_dir = os.path.dirname(android_private)
    dst_llama_dir = os.path.join(files_dir, "native_libs")

    _early_log(f"_extract_native_libs: project_dir={project_dir}")
    _early_log(f"_extract_native_libs: src_llama_dir={src_llama_dir}")
    _early_log(f"_extract_native_libs: src_llama_dir exists={os.path.exists(src_llama_dir)}")
    _early_log(f"_extract_native_libs: files_dir={files_dir}")
    _early_log(f"_extract_native_libs: dst_llama_dir={dst_llama_dir}")


    if os.path.exists(src_llama_dir):
        try:
            src_files = os.listdir(src_llama_dir)
            _early_log(f"_extract_native_libs: src files: {src_files}")
        except Exception as e:
            _early_log(f"_extract_native_libs: failed to list src: {e}")

    libs = ["libomp.so", "libggml-base.so", "libggml-cpu.so", "libggml.so", "libllama.so"]

    try:
        os.makedirs(dst_llama_dir, exist_ok=True)
        _early_log(f"_extract_native_libs: created dst dir")

        copied_count = 0
        for lib in libs:
            src_path = os.path.join(src_llama_dir, lib)
            dst_path = os.path.join(dst_llama_dir, lib)

            _early_log(f"_extract_native_libs: checking {lib}: src_exists={os.path.exists(src_path)}, dst_exists={os.path.exists(dst_path)}")


            need_copy = False
            if not os.path.exists(dst_path):
                need_copy = True
            elif os.path.exists(src_path):
                src_size = os.path.getsize(src_path)
                dst_size = os.path.getsize(dst_path)
                if src_size != dst_size:
                    need_copy = True
                    _early_log(f"_extract_native_libs: {lib} size mismatch: src={src_size}, dst={dst_size}")

            if need_copy and os.path.exists(src_path):
                _early_log(f"_extract_native_libs: copying {lib} (binary mode)...")

                with open(src_path, 'rb') as sf:
                    data = sf.read()
                with open(dst_path, 'wb') as df:
                    df.write(data)

                os.chmod(dst_path, 0o755)
                _early_log(f"_extract_native_libs: {lib} copied OK, size={os.path.getsize(dst_path)}")
                copied_count += 1
            elif os.path.exists(dst_path):
                _early_log(f"_extract_native_libs: {lib} already exists, size={os.path.getsize(dst_path)}")
            else:
                _early_log(f"_extract_native_libs: {lib} NOT FOUND at {src_path}")


        final_lib_path = os.path.join(dst_llama_dir, "libllama.so")
        if os.path.exists(final_lib_path):
            _early_log(f"_extract_native_libs: done, copied {copied_count} files, libllama.so OK")
            return dst_llama_dir
        else:
            _early_log(f"_extract_native_libs: FAILED - libllama.so not in dst after copy")
            return ""
    except Exception as e:
        _early_log(f"_extract_native_libs: FAILED: {e}")
        _early_log(traceback.format_exc())
        return ""


def _setup_android_llama() -> None:
    """Настройка llama библиотек для Android. Безопасно обёрнуто в try/except."""
    if not _is_android():
        return

    _early_log("_setup_android_llama: starting...")

    try:
        project_dir = os.path.dirname(os.path.abspath(__file__))
        third_party_dir = os.path.join(project_dir, "third_party")
        if third_party_dir not in sys.path:
            sys.path.insert(0, third_party_dir)
        _early_log(f"_setup_android_llama: third_party_dir={third_party_dir}")



        llama_dir = _find_system_native_libs()


        if not llama_dir:
            _early_log("_setup_android_llama: system libs not found, trying extraction from assets...")
            llama_dir = _extract_native_libs_android()


        if llama_dir:
            lib_path = os.path.join(llama_dir, "libllama.so")
            _early_log(f"_setup_android_llama: using libs from {llama_dir}")
            _early_log(f"_setup_android_llama: libllama.so exists={os.path.exists(lib_path)}")


            if os.path.exists(lib_path):

                os.environ["LLAMA_CPP_LIB_PATH"] = llama_dir
                os.environ["LLAMA_CPP_LIB"] = lib_path
                existing = os.environ.get("LD_LIBRARY_PATH", "")
                if llama_dir not in existing.split(":" if existing else ""):
                    os.environ["LD_LIBRARY_PATH"] = (llama_dir + ":" + existing).strip(":")
                _early_log(f"_setup_android_llama: LLAMA_CPP_LIB_PATH={llama_dir}")
                _early_log(f"_setup_android_llama: LLAMA_CPP_LIB={lib_path}")
                _early_log(f"_setup_android_llama: LD_LIBRARY_PATH={os.environ.get('LD_LIBRARY_PATH', '')}")



                all_deps_loaded = True
                for dep in ("libomp.so", "libggml-base.so", "libggml-cpu.so", "libggml.so"):
                    dep_path = os.path.join(llama_dir, dep)
                    if os.path.exists(dep_path):
                        try:
                            _early_log(f"_setup_android_llama: loading {dep} from {dep_path}...")
                            ctypes.CDLL(dep_path, mode=ctypes.RTLD_GLOBAL)
                            _early_log(f"_setup_android_llama: {dep} loaded OK")
                        except Exception as e:
                            _early_log(f"_setup_android_llama: {dep} FAILED: {e}")
                            all_deps_loaded = False
                    else:
                        _early_log(f"_setup_android_llama: {dep} NOT FOUND at {dep_path}")
                        all_deps_loaded = False


                if all_deps_loaded:
                    try:
                        _early_log(f"_setup_android_llama: loading libllama.so from {lib_path}...")
                        _llama_lib = ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
                        _early_log(f"_setup_android_llama: libllama.so loaded OK!")

                        os.environ["_LLAMA_LIB_LOADED"] = "1"
                        os.environ["_LLAMA_ALL_LOADED"] = "1"
                    except Exception as e:
                        _early_log(f"_setup_android_llama: libllama.so FAILED: {e}")
                        os.environ["_LLAMA_LOAD_ERROR"] = str(e)[:200]
                else:
                    _early_log(f"_setup_android_llama: skipping libllama.so load - deps not loaded")
            else:
                _early_log(f"_setup_android_llama: libllama.so NOT FOUND in {llama_dir}")
        else:

            _early_log(f"_setup_android_llama: WARNING - no native libs found, offline AI will not work")
            _early_log(f"_setup_android_llama: NOT setting LLAMA_CPP_LIB to avoid misleading errors")

        _early_log("_setup_android_llama: done")
    except Exception as e:
        _early_log(f"_setup_android_llama: EXCEPTION: {e}")
        _early_log(traceback.format_exc())



if os.environ.get("MM_EAGER_LLAMA_SETUP", "0") == "1":
    try:
        _setup_android_llama()
    except Exception as e:
        _early_log(f"_setup_android_llama call FAILED: {e}")


def _startup_log_path() -> str:
    android_private = os.environ.get("ANDROID_PRIVATE")
    if android_private:
        return os.path.join(android_private, "startup_crash.log")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "startup_crash.log")


def _log_startup_exception(exc: BaseException) -> None:
    try:
        log_path = _startup_log_path()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("\n=== STARTUP EXCEPTION ===\n")
            f.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
            f.write("\n")
    except Exception:
        pass


def _excepthook(exc_type, exc, tb) -> None:
    if isinstance(exc, BaseException):
        _log_startup_exception(exc)
    else:
        try:
            log_path = _startup_log_path()
            with open(log_path, "a", encoding="utf-8") as f:
                f.write("\n=== STARTUP EXCEPTION ===\n")
                f.write("".join(traceback.format_exception(exc_type, exc, tb)))
                f.write("\n")
        except Exception:
            pass
    sys.__excepthook__(exc_type, exc, tb)


sys.excepthook = _excepthook


_early_log("Setting up environment variables...")
if _is_android():

    os.environ.setdefault('SDL_RENDER_DRIVER', 'software')
    os.environ.setdefault('KIVY_GL_BACKEND', 'gl')
    os.environ.setdefault('SDL_RENDER_BATCHING', '0')
    os.environ.setdefault('SDL_HINT_RENDER_DRIVER', 'software')
    _early_log("Android env vars set")
else:

    os.environ.setdefault('KIVY_GL_BACKEND', 'gl')
    _early_log("Desktop env vars set")


_early_log("Importing kivy.config...")
try:
    from kivy.config import Config
    Config.set('graphics', 'multisamples', '0')
    if _is_android():
        Config.set('kivy', 'pause_on_minimize', '0')
    _early_log("kivy.config OK")
except Exception as e:
    _early_log(f"kivy.config FAILED: {e}")
    _early_log(traceback.format_exc())
    raise

_early_log("Importing standard libs...")
import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional, cast
_early_log("Standard libs OK")

_early_log("Importing kivy modules...")
try:
    from kivy.clock import Clock
    from kivy.lang import Builder
    from kivy.properties import BooleanProperty, DictProperty, StringProperty
    from kivy.uix.screenmanager import ScreenManager, SlideTransition
    _early_log("kivy modules OK")
except Exception as e:
    _early_log(f"kivy modules FAILED: {e}")
    _early_log(traceback.format_exc())
    raise

_early_log("Importing kivymd...")
try:
    from kivymd.app import MDApp
    from kivymd.uix.dialog import MDDialog
    from kivymd.uix.dialog.dialog import (
        MDDialogHeadlineText,
        MDDialogSupportingText,
        MDDialogButtonContainer,
    )
    from kivymd.uix.button import MDButton, MDButtonText
    from kivymd.uix.snackbar import MDSnackbar
    _early_log("kivymd OK")
except Exception as e:
    _early_log(f"kivymd FAILED: {e}")
    _early_log(traceback.format_exc())
    raise


_early_log("Importing screens...")
try:
    from screens.home_screen import HomeScreen
    from screens.courses_screen import CoursesScreen
    from screens.course_topic_screen import CourseTopicScreen
    from screens.theory_screen import TheoryScreen
    from screens.quiz_screen import QuizScreen
    from screens.quiz_selection_screen import QuizSelectionScreen
    from screens.tests_selection_screen import TestsSelectionScreen
    from screens.stats_screen import StatsScreen
    from screens.molecules_screen import MoleculesScreen
    from screens.molecule_viewer_screen import MoleculeViewerScreen
    from screens.molecule_editor_screen import MoleculeEditorScreen
    from screens.reactions_screen import ReactionsScreen
    from screens.reaction_viewer_screen import ReactionViewerScreen
    from screens.reaction_editor_screen import ReactionEditorScreen
    from screens.favorites_screen import FavoritesScreen
    from screens.ai_assistant_screen import AIAssistantScreen
    from screens.model_download_screen import ModelDownloadScreen
    _early_log("screens OK")
except Exception as e:
    _early_log(f"screens FAILED: {e}")
    _early_log(traceback.format_exc())
    raise

_early_log("Importing utils...")
try:
    from utils.ai_engine import AIEngine
    from utils.course_repo import CourseRepo
    from utils.model_bootstrap import ensure_gguf_ready, needs_download, get_available_model_path
    from theme import THEME
    _early_log("utils OK")
except Exception as e:
    _early_log(f"utils FAILED: {e}")
    _early_log(traceback.format_exc())
    raise

_early_log("All imports completed successfully!")



PROJECT_DIR = Path(__file__).resolve().parent
_early_log(f"PROJECT_DIR: {PROJECT_DIR}")

KV_PATH = PROJECT_DIR / "kv" / "main.kv"
COURSES_DB = PROJECT_DIR / "data" / "courses" / "courses.db"
HF_TOKEN = PROJECT_DIR / "data" / "secrets" / "hf_token.txt"


OFFLINE_MODEL_NAME = "Llama-3.2-1B-Instruct-Q4_K_M.gguf"

MOLECULES_DIR = PROJECT_DIR / "assets" / "molecules"
REACTIONS_DIR = PROJECT_DIR / "assets" / "reactions"

# Проверяем критические файлы сразу
_early_log(f"KV_PATH: {KV_PATH}, exists: {KV_PATH.exists()}")
_early_log(f"COURSES_DB: {COURSES_DB}, exists: {COURSES_DB.exists()}")
_early_log(f"MOLECULES_DIR: {MOLECULES_DIR}, exists: {MOLECULES_DIR.exists()}")
_early_log(f"REACTIONS_DIR: {REACTIONS_DIR}, exists: {REACTIONS_DIR.exists()}")


_early_log(f"KV_PATH: {KV_PATH}, exists: {KV_PATH.exists()}")
_early_log(f"COURSES_DB: {COURSES_DB}, exists: {COURSES_DB.exists()}")
_early_log(f"MOLECULES_DIR: {MOLECULES_DIR}, exists: {MOLECULES_DIR.exists()}")
_early_log(f"REACTIONS_DIR: {REACTIONS_DIR}, exists: {REACTIONS_DIR.exists()}")


def _db_conn(db_path: str) -> sqlite3.Connection:
    """Подключаемся к базе данных"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def ensure_mm_tables(db_path: str) -> None:
    """Создаём таблицы для тестов, если их ещё нет"""
    with _db_conn(db_path) as conn:
        cur = conn.cursor()


        cur.execute("""
        CREATE TABLE IF NOT EXISTS mm_app_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """)


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
        
        # Создаем запись-заглушку для викторин по категориям (quiz_id=0)
        # Это нужно для foreign key constraint в mm_quiz_attempts
        # Используем course_id из существующего курса (или 1 по умолчанию)
        cur.execute("""
        INSERT OR IGNORE INTO mm_quizzes (id, course_id, title) 
        SELECT 0, COALESCE((SELECT id FROM courses LIMIT 1), 1), 'Викторины по категориям'
        WHERE NOT EXISTS (SELECT 1 FROM mm_quizzes WHERE id = 0)
        """)






        cur.execute("""
        INSERT OR IGNORE INTO mm_quizzes (id, course_id, title)
        SELECT 0, (SELECT id FROM courses LIMIT 1), 'Викторины по категориям'
        WHERE EXISTS (SELECT 1 FROM courses)
          AND NOT EXISTS (SELECT 1 FROM mm_quizzes WHERE id = 0)
        """)

        conn.commit()



APP_DATA_VERSION = "3"


def reset_quiz_history_if_needed(db_path: str) -> bool:
    """
    Сбрасывает историю тестов/викторин при первом запуске или обновлении версии.
    Возвращает True, если история была сброшена.
    """
    with _db_conn(db_path) as conn:
        cur = conn.cursor()


        row = cur.execute(
            "SELECT value FROM mm_app_meta WHERE key='data_version'"
        ).fetchone()

        current_version = row["value"] if row else None

        if current_version == APP_DATA_VERSION:
            return False


        _early_log(f"Resetting quiz history (version {current_version} -> {APP_DATA_VERSION})")

        cur.execute("DELETE FROM mm_quiz_attempts")
        cur.execute("""
            UPDATE mm_course_progress
            SET best_percent=0, last_percent=0, attempts_count=0,
                updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
        """)


        cur.execute(
            "INSERT OR REPLACE INTO mm_app_meta (key, value) VALUES ('data_version', ?)",
            (APP_DATA_VERSION,)
        )

        conn.commit()
        _early_log("Quiz history reset complete")
        return True


def seed_section_quizzes_if_needed(db_path: str) -> bool:
    """Создаёт тесты для разделов курса, если их ещё нет."""
    import json

    with _db_conn(db_path) as conn:
        cur = conn.cursor()


        existing = cur.execute(
            "SELECT COUNT(*) FROM mm_quizzes WHERE section_id IS NOT NULL"
        ).fetchone()[0]

        if existing > 0:
            return False

        _early_log("Creating section quizzes...")

        try:
            from data.quiz_questions import get_questions_by_section
        except ImportError:
            _early_log("Cannot import quiz_questions - skipping section quizzes")
            return False


        sections = cur.execute(
            "SELECT id, course_id, title FROM course_sections ORDER BY id"
        ).fetchall()

        created_count = 0
        for s in sections:
            section_id = int(s["id"])
            course_id = int(s["course_id"])
            title = str(s["title"])


            questions = get_questions_by_section(section_id)

            if len(questions) < 5:
                _early_log(f"Skipping section {section_id} ({title}) - only {len(questions)} questions")
                continue


            quiz_title = f"Тест: {title}"
            cur.execute(
                "INSERT INTO mm_quizzes (course_id, section_id, title) VALUES (?, ?, ?)",
                (course_id, section_id, quiz_title)
            )
            quiz_id = cur.lastrowid


            for i, q in enumerate(questions):
                cur.execute(
                    """INSERT INTO mm_quiz_questions
                       (quiz_id, order_index, q, options_json, correct_index, explanation)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (quiz_id, i, q['q'], json.dumps(q['options'], ensure_ascii=False),
                     q['correct'], q.get('explanation', ''))
                )

            created_count += 1
            _early_log(f"Created quiz '{quiz_title}' with {len(questions)} questions")

        conn.commit()
        _early_log(f"Created {created_count} section quizzes")
        return created_count > 0


def seed_quizzes_if_needed(db_path: str) -> bool:
    """Заполняем базу вопросами, если она пустая"""
    with _db_conn(db_path) as conn:
        cur = conn.cursor()
        q_count = int(cur.execute("select count(*) from mm_quiz_questions").fetchone()[0])
        if q_count > 0:
            return False

        courses = cur.execute("select id, title from courses order by id").fetchall()
        if not courses:
            return False


        base_questions = [
            (
                "Какая связь образуется при боковом перекрытии p-орбиталей?",
                ["Сигма-связь", "Пи-связь", "Ионная связь", "Водородная связь"],
                1,
                "Пи-связь образуется при боковом перекрытии p-орбиталей.",
            ),
            (
                "Алканы относятся к:",
                ["Ненасыщенным углеводородам", "Насыщенным углеводородам", "Кислородсодержащим соединениям", "Азотсодержащим соединениям"],
                1,
                "Алканы содержат только одинарные связи и являются насыщенными.",
            ),
            (
                "Изомерия — это:",
                ["Разный состав", "Одинаковый состав и разное строение", "Одинаковое строение и разная масса", "Только разное агрегатное состояние"],
                1,
                "Изомеры имеют одинаковую формулу, но различаются строением или пространственным расположением.",
            ),
            (
                "Фенолы дают характерную окраску с:",
                ["FeCl3", "NaHCO3", "AgNO3", "KMnO4"],
                0,
                "Фенолы образуют окрашенные комплексы с FeCl3.",
            ),
            (
                "Карбоновые кислоты с карбонатами выделяют газ:",
                ["H2", "CO2", "NH3", "Cl2"],
                1,
                "Кислота + карбонат -> CO2 + соль + вода.",
            ),
            (
                "Степень окисления — это:",
                ["Число связей атома", "Условный заряд атома в соединении", "Реальный заряд иона", "Число нейтронов"],
                1,
                "Степень окисления — условный заряд при допущении ионного характера связей.",
            ),
            (
                "Принцип Ле Шателье описывает:",
                ["Скорость реакции", "Смещение равновесия при изменении условий", "Растворимость", "Только каталитические реакции"],
                1,
                "При внешнем воздействии равновесие смещается в сторону ослабления воздействия.",
            ),
            (
                "Катализатор в реакции:",
                ["Смещает равновесие", "Уменьшает энергию активации", "Всегда расходуется полностью", "Делает реакцию эндотермической"],
                1,
                "Катализатор снижает энергию активации и ускоряет реакцию, не смещая равновесие.",
            ),
        ]


        for course in courses:
            course_id = int(course["id"])
            title = str(course["title"])
            quiz_title = f"Итоговый тест: {title}"

            cur.execute("insert into mm_quizzes(course_id, title) values (?, ?)", (course_id, quiz_title))
            quiz_rowid = cur.lastrowid
            if quiz_rowid is None:
                raise RuntimeError("Не удалось создать тест (mm_quizzes)")
            quiz_id = int(quiz_rowid)

            for idx, (q, opts, correct, expl) in enumerate(base_questions, start=1):
                cur.execute(
                    "insert into mm_quiz_questions(quiz_id, q, options_json, correct_index, explanation, order_index) "
                    "values (?, ?, ?, ?, ?, ?)",
                    (quiz_id, q, json.dumps(opts, ensure_ascii=False), int(correct), expl, idx),
                )

        conn.commit()
        return True


class MoleculeMentorApp(MDApp):
    """Главный класс приложения"""

    top_title = StringProperty("Molecule Mentor")
    back_visible = BooleanProperty(False)
    ai_status = StringProperty("N/A")
    ai_status_phase = StringProperty("checking")
    ai_status_display = StringProperty("Идет проверка...")
    nav_state = DictProperty({})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


        self.project_dir = str(PROJECT_DIR)
        self.courses_db = str(COURSES_DB)
        self.molecules_dir = str(MOLECULES_DIR)
        self.reactions_dir = str(REACTIONS_DIR)


        self.mm_bg = THEME.bg
        self.mm_surface = THEME.surface
        self.mm_surface2 = THEME.surface2
        self.mm_primary = THEME.primary
        self.mm_accent = THEME.accent
        self.mm_button_color = THEME.button_color
        self.mm_text = THEME.text
        self.mm_text2 = THEME.text2


        self.mm_molecules_card_bg = self.mm_surface2
        self.mm_molecules_card_border = (1, 1, 1, 0.16)
        self.mm_molecules_card_pressed_delta = 0.08
        self.mm_molecules_card_elevation = 2
        self.mm_molecules_list_spacing = 4
        self.mm_molecules_list_bottom_padding = 8


        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mm")
        self._ai_engine: Optional[AIEngine] = None
        self._ai_dialog: Optional[MDDialog] = None
        self._download_prompt_dialog: Optional[MDDialog] = None
        self._ai_lock = threading.RLock()


        _early_log(f"MoleculeMentorApp.__init__: checking COURSES_DB={COURSES_DB}")
        if not COURSES_DB.exists():
            _early_log(f"COURSES_DB NOT FOUND!")
            raise FileNotFoundError(f"База курсов не найдена: {COURSES_DB}")

        _early_log("MoleculeMentorApp.__init__: ensuring tables...")
        ensure_mm_tables(self.courses_db)

        _early_log("MoleculeMentorApp.__init__: checking for quiz history reset...")
        reset_quiz_history_if_needed(self.courses_db)

        _early_log("MoleculeMentorApp.__init__: seeding section quizzes if needed...")
        seed_section_quizzes_if_needed(self.courses_db)

        _early_log("MoleculeMentorApp.__init__: creating CourseRepo...")
        self.course_repo = CourseRepo(self.courses_db)
        self._nav_stack: list[str] = ["home"]
        _early_log("MoleculeMentorApp.__init__: done")

    def build(self):
        """Строим интерфейс приложения"""
        _early_log("MoleculeMentorApp.build: starting...")
        self.theme_cls.material_style = "M3"

        _early_log(f"MoleculeMentorApp.build: checking KV_PATH={KV_PATH}")
        if not KV_PATH.exists():
            _early_log(f"KV_PATH NOT FOUND!")
            raise FileNotFoundError(f"KV файл не найден: {KV_PATH}")

        _early_log("MoleculeMentorApp.build: loading KV file...")
        try:
            root = cast(Any, Builder.load_file(str(KV_PATH)))
            _early_log("MoleculeMentorApp.build: KV loaded OK")
        except Exception as e:
            _early_log(f"MoleculeMentorApp.build: KV load FAILED: {e}")
            _early_log(traceback.format_exc())
            raise
        root_ids = getattr(root, "ids", None)
        if not root_ids or "sm" not in root_ids:
            _early_log("ScreenManager 'sm' NOT FOUND in KV!")
            raise RuntimeError("ScreenManager id 'sm' не найден в KV")
        sm = cast(ScreenManager, root_ids.sm)
        _early_log("MoleculeMentorApp.build: ScreenManager OK")


        _early_log("MoleculeMentorApp.build: adding screens...")
        try:
            sm.add_widget(HomeScreen(name="home"))
            sm.add_widget(CoursesScreen(name="courses"))
            sm.add_widget(CourseTopicScreen(name="course_topic"))
            sm.add_widget(TheoryScreen(name="theory"))
            sm.add_widget(QuizScreen(name="quiz"))
            sm.add_widget(QuizSelectionScreen(name="quiz_selection"))
            sm.add_widget(TestsSelectionScreen(name="tests_selection"))
            sm.add_widget(StatsScreen(name="stats"))
            sm.add_widget(FavoritesScreen(name="favorites"))
            sm.add_widget(MoleculesScreen(name="molecules"))
            sm.add_widget(MoleculeViewerScreen(name="molecule_viewer"))
            sm.add_widget(MoleculeEditorScreen(name="molecule_editor"))
            sm.add_widget(ReactionsScreen(name="reactions"))
            sm.add_widget(ReactionViewerScreen(name="reaction_viewer"))
            sm.add_widget(ReactionEditorScreen(name="reaction_editor"))
            sm.add_widget(AIAssistantScreen(name="ai_assistant"))
            sm.add_widget(ModelDownloadScreen(name="model_download"))
            _early_log("MoleculeMentorApp.build: all screens added OK")
        except Exception as e:
            _early_log(f"MoleculeMentorApp.build: adding screens FAILED: {e}")
            _early_log(traceback.format_exc())
            raise

        sm.current = "home"
        _early_log("MoleculeMentorApp.build: done, returning root")
        return root

    def on_start(self):
        """Запускается при старте приложения"""

        # Не делаем eager-инициализацию llama на старте, чтобы избежать
        # нативных падений на части устройств. Инициализация произойдет
        # лениво при первом обращении к оффлайн-ИИ.

        try:
            Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print("[WARN] не удалось создать папку данных:", e)


        preferred_model_path = get_available_model_path(OFFLINE_MODEL_NAME)
        if preferred_model_path is not None:
            offline_target = str(preferred_model_path)
        else:
            offline_target = str(Path(self.user_data_dir).resolve() / "models" / OFFLINE_MODEL_NAME)

        self._ai_engine = AIEngine(
            hf_token_path=str(HF_TOKEN),
            offline_model_path=offline_target,
        )


        need_dl = needs_download(OFFLINE_MODEL_NAME)
        print(f"[STARTUP] нужна загрузка модели: {need_dl}")
        if need_dl:
            print("[STARTUP] показываем окно загрузки")
            self._show_download_prompt_on_start()
        else:
            print("[STARTUP] модель уже доступна")
            self._refresh_ai_status_async()


        Clock.schedule_interval(lambda *_: self._refresh_ai_status_async(), 15.0)
        self._refresh_ai_status_async()


        self._executor.submit(self._seed_quizzes_background)

        self.set_top_title("Главная")
        self.set_back_visible(False)

    def _show_download_prompt_on_start(self) -> None:
        """Показывает окно с предложением скачать оффлайн-модель."""
        def show_prompt(_dt):
            if self._download_prompt_dialog:
                try:
                    self._download_prompt_dialog.dismiss()
                except Exception:
                    pass

            def on_later(*_):
                self._dismiss_download_prompt()

            def on_download(*_):
                self._dismiss_download_prompt()
                self._start_offline_download_flow()

            self._download_prompt_dialog = MDDialog(
                MDDialogHeadlineText(text="Скачать оффлайн-модель ИИ?"),
                MDDialogSupportingText(
                    text="Чтобы ИИ работал без интернета, скачайте модель (~1.9 ГБ)."
                ),
                MDDialogButtonContainer(
                    MDButton(
                        MDButtonText(text="Позже"),
                        style="text",
                        on_release=on_later,
                    ),
                    MDButton(
                        MDButtonText(text="Скачать"),
                        style="text",
                        on_release=on_download,
                    ),
                ),
            )
            self._download_prompt_dialog.open()

        Clock.schedule_once(show_prompt, 0.6)

    def _dismiss_download_prompt(self) -> None:
        if not self._download_prompt_dialog:
            return
        try:
            self._download_prompt_dialog.dismiss()
        except Exception:
            pass
        self._download_prompt_dialog = None

    def _start_offline_download_flow(self) -> None:
        """Открывает экран загрузки и запускает скачивание."""
        self.open_model_download()

        def kick(_dt):
            try:
                scr = self._sm().get_screen("model_download")
                if hasattr(scr, "start_download"):
                    scr.start_download()
            except Exception:
                pass

        Clock.schedule_once(kick, 0.2)

    def _prepare_offline_model_async(self) -> None:
        """Собираем модель из частей в фоновом потоке"""
        def work():
            try:
                print("[OFFLINE] собираю модель...")
                p = ensure_gguf_ready(OFFLINE_MODEL_NAME)
                print(f"[OFFLINE] модель готова: {p}")
                if self._ai_engine:
                    self._ai_engine.set_offline_model_path(str(p))

                def notify(_dt):
                    self.toast("Оффлайн модель готова")
                    self._refresh_ai_status_async()

                Clock.schedule_once(notify, 0)
            except Exception as e:
                import traceback
                print(f"[OFFLINE] ошибка: {e}")
                traceback.print_exc()
                err_text = str(e)

                def notify_err(_dt):
                    self.toast(f"Оффлайн модель недоступна: {err_text}")
                    self._refresh_ai_status_async()

                Clock.schedule_once(notify_err, 0)

        self._executor.submit(work)

    def on_stop(self):
        """При закрытии приложения"""
        try:
            if self._ai_engine:
                self._ai_engine.stop()
        except Exception:
            pass
        try:
            self._executor.shutdown(wait=True, cancel_futures=True)
        except Exception:
            pass

    def toast(self, text: str) -> None:
        """Показываем всплывающее сообщение"""
        try:
            MDSnackbar(text=text, y=24).open()
        except Exception:
            print("[MSG]", text)

    def _sm(self) -> ScreenManager:
        """Получаем менеджер экранов"""
        assert self.root is not None
        root = cast(Any, self.root)
        root_ids = getattr(root, "ids", None)
        if not root_ids or "sm" not in root_ids:
            raise RuntimeError("ScreenManager id 'sm' не найден в root")
        return cast(ScreenManager, root_ids.sm)

    def set_top_title(self, title: str) -> None:
        """Устанавливаем заголовок в шапке"""
        self.top_title = title

    def set_back_visible(self, visible: bool) -> None:
        """Показать/скрыть кнопку назад"""
        self.back_visible = bool(visible)

    def _set_screen(self, name: str, push: bool = True, force: bool = False) -> None:
        """Переключаемся на другой экран"""
        sm = self._sm()


        if sm.current == name:
            if force:
                try:
                    scr = sm.get_screen(name)
                    if hasattr(scr, "refresh"):
                        scr.refresh()
                    else:
                        scr.dispatch("on_pre_enter")
                except Exception:
                    pass
            return

        sm.transition = SlideTransition(direction="left")
        sm.current = name


        if push and (not self._nav_stack or self._nav_stack[-1] != name):
            self._nav_stack.append(name)

        self.set_back_visible(name != "home")

    def go_back(self) -> None:
        """Возврат на предыдущий экран"""
        if len(self._nav_stack) <= 1:
            self.open_home()
            return

        current = self._nav_stack.pop()
        prev = self._nav_stack[-1]


        st = dict(self.nav_state or {})
        if current == "theory":
            st.pop("topic_id", None)
            st.pop("topic_title", None)
        elif current == "course_topic" and st.get("section_id"):
            st.pop("section_id", None)
            st.pop("section_title", None)
        self.nav_state = st

        sm = self._sm()
        sm.transition = SlideTransition(direction="right")
        sm.current = prev


        try:
            scr = sm.get_screen(prev)
            if hasattr(scr, "on_pre_enter"):
                scr.dispatch("on_pre_enter")
        except Exception:
            pass

        self.set_back_visible(prev != "home")



    def open_home(self) -> None:
        """На главную"""
        self.nav_state = {}
        self._nav_stack = ["home"]
        self.set_top_title("Главная")
        self._set_screen("home", push=False)

    def open_courses(self) -> None:
        """Открыть курсы"""
        self.nav_state = {}
        self.set_top_title("Курсы")
        self._set_screen("courses")

    def open_molecules(self) -> None:
        """Открыть библиотеку молекул"""
        self.nav_state = {}
        self.set_top_title("Молекулы")
        self._set_screen("molecules")

    def open_molecule_viewer(self, pdb_path: str, title: str, description: str = "") -> None:
        """Открыть 3D просмотр молекулы"""
        self.nav_state = {"pdb_path": pdb_path, "title": title, "description": description}
        self.set_top_title(title)
        self._set_screen("molecule_viewer")

    def open_molecule_editor(self, pdb_path: str, title: str) -> None:
        """Открыть редактор молекулы"""
        self.nav_state = {"pdb_path": pdb_path, "title": title}
        self.set_top_title(title)
        self._set_screen("molecule_editor")

    def open_reactions(self) -> None:
        """Открыть библиотеку реакций"""
        self.nav_state = {}
        self.set_top_title("Реакции")
        self._set_screen("reactions")

    def open_reaction_viewer(self, reaction_id: str, title: str) -> None:
        """Открыть просмотр реакции"""
        self.nav_state = {"reaction_id": str(reaction_id), "title": str(title)}
        self.set_top_title(title)
        self._set_screen("reaction_viewer")

    def open_reaction_editor(self) -> None:
        """Открыть редактор реакций"""
        self.nav_state = {}
        self.set_top_title("Похимичим!")
        self._set_screen("reaction_editor")

    def open_ai_assistant(self) -> None:
        """Открыть чат с ИИ"""
        self.set_top_title("ИИ-помощник")
        self._set_screen("ai_assistant")

    def open_model_download(self) -> None:
        """Открыть экран загрузки модели"""
        self.set_top_title("Загрузка модели")
        self._set_screen("model_download")

    def open_course(self, course_id: int, course_title: str) -> None:
        """Открыть курс (список разделов)"""
        st = dict(self.nav_state or {})
        st["course_id"] = int(course_id)
        st["course_title"] = str(course_title)
        st.pop("section_id", None)
        st.pop("section_title", None)
        st.pop("topic_id", None)
        st.pop("topic_title", None)
        self.nav_state = st
        self.set_top_title(course_title)
        self._set_screen("course_topic")

    def open_section(self, section_id: int, section_title: str) -> None:
        """Открыть раздел курса (список тем)"""
        st = dict(self.nav_state or {})
        st["section_id"] = int(section_id)
        st["section_title"] = str(section_title)
        st.pop("topic_id", None)
        st.pop("topic_title", None)
        self.nav_state = st
        self.set_top_title(section_title)
        self._set_screen("course_topic", force=True)

    def open_topic(self, topic_id: int, topic_title: str) -> None:
        """Открыть тему (теория)"""
        st = dict(self.nav_state or {})
        st["topic_id"] = int(topic_id)
        st["topic_title"] = str(topic_title)
        self.nav_state = st
        self.set_top_title(topic_title)
        self._set_screen("theory")

    def open_quiz_for_course(self, course_id: int) -> None:
        """Открыть тест по курсу"""
        self.nav_state = {"course_id": int(course_id)}
        self.set_top_title("Тест")
        self._set_screen("quiz")

    def open_tests_selection(self) -> None:
        """Открыть экран выбора тестов"""
        self.nav_state = {}
        self.set_top_title("Тесты")
        self._set_screen("tests_selection")

    def open_quiz_for_section(self, section_id: int, section_title: str) -> None:
        """Открыть тест по разделу курса"""
        self.nav_state = {"section_id": int(section_id), "section_title": str(section_title)}
        self.set_top_title("Тест")
        self._set_screen("quiz")

    def open_quiz_selection(self) -> None:
        """Открыть экран выбора викторин"""
        self.nav_state = {}
        self.set_top_title("Викторины")
        self._set_screen("quiz_selection")

    def open_quiz_standalone(self) -> None:
        """Открыть викторину (режим по категории)"""
        title = str(self.nav_state.get("quiz_title", "Викторина"))
        self.set_top_title(title)
        self._set_screen("quiz")

    def open_stats(self) -> None:
        """Открыть статистику и достижения"""
        self.nav_state = {}
        self.set_top_title("Статистика")
        self._set_screen("stats")

    def open_favorites(self) -> None:
        """Открыть избранное"""
        self.nav_state = {}
        self.set_top_title("Избранное")
        self._set_screen("favorites")



    def _refresh_ai_status_async(self) -> None:
        """Обновляем статус ИИ"""
        if not self._ai_engine:
            self.ai_status = "N/A"
            self.ai_status_phase = "na"
            self.ai_status_display = "НЕТ"
            return


        if self.ai_status in ("N/A", ""):
            self.ai_status_phase = "checking"
            self.ai_status_display = "..."

        fut = self._executor.submit(self._ai_engine.diagnose)

        def on_done(_dt):
            try:
                d = fut.result()
                mode = str(getattr(d, "mode", "N/A"))
                if mode == "N/A" and not getattr(d, "online_reachable", True):
                    mode = "OFFLINE"
                self.ai_status = mode

                if mode == "ONLINE":
                    self.ai_status_phase = "online"
                    self.ai_status_display = "ОНЛ"
                elif mode == "OFFLINE":
                    self.ai_status_phase = "offline"
                    self.ai_status_display = "ОФФ"
                else:
                    self.ai_status_phase = "na"
                    self.ai_status_display = "НЕТ"
            except Exception:
                self.ai_status = "N/A"
                self.ai_status_phase = "na"
                self.ai_status_display = "НЕТ"

        Clock.schedule_once(on_done, 0)

    def on_ai_status(self, _inst, value: str) -> None:
        """Лёгкий пульс индикатора статуса ИИ."""
        try:

            from kivy.animation import Animation

            root = self.root
            if not root:
                return
            ico = getattr(root, "ids", {}).get("ai_info_icon")
            if not ico:
                return

            Animation.cancel_all(ico, "opacity")
            seq = Animation(opacity=0.40, d=0.10, t="out_quad") + Animation(opacity=1.0, d=0.40, t="out_cubic")
            seq.start(ico)
        except Exception:
            return

    def show_ai_info(self) -> None:
        """Показываем информацию о состоянии ИИ"""
        if not self._ai_engine:
            self.toast("ИИ ещё не готов")
            return

        fut = self._executor.submit(self._ai_engine.diagnose)

        def on_done(_dt):
            try:
                d = fut.result()
                data = asdict(d)


                mode = data.get('mode', 'N/A')
                online_ok = data.get('online_reachable', False)
                offline_ok = data.get('offline_model_exists', False) and data.get('llama_import_ok', False)


                if mode == "ONLINE":
                    status_text = "Онлайн (HuggingFace)"
                elif mode == "OFFLINE":
                    status_text = "Оффлайн (локальная модель)"
                else:
                    status_text = "Не определён"

                lines = [f"Режим: {status_text}"]


                if online_ok:
                    lines.append("Интернет: доступен")
                else:
                    lines.append("Интернет: недоступен")


                if data.get('offline_model_exists'):
                    if data.get('llama_import_ok'):
                        lines.append("Оффлайн-модель: готова к работе")
                    else:
                        lines.append("Оффлайн-модель: скачана, но не загружена")
                else:
                    lines.append("Оффлайн-модель: не скачана")


                if not online_ok and not offline_ok:
                    lines.append("")
                    lines.append("Подключите интернет или скачайте оффлайн-модель")
                elif not online_ok and offline_ok:
                    lines.append("")
                    lines.append("ИИ работает в оффлайн-режиме")


                if data.get("llama_last_error") and not data.get('llama_import_ok'):
                    err = str(data.get('llama_last_error', ''))

                    if "undefined symbol" in err:
                        lines.append("")
                        lines.append("Ошибка: несовместимая версия библиотеки")
                    elif "not found" in err.lower():
                        lines.append("")
                        lines.append("Ошибка: библиотека не найдена")

                msg = "\n".join(lines)
            except Exception as e:
                msg = f"Ошибка диагностики: {e}"

            if self._ai_dialog:
                try:
                    self._ai_dialog.dismiss()
                except Exception:
                    pass

            self._ai_dialog = MDDialog(
                MDDialogHeadlineText(text="ИИ: диагностика"),
                MDDialogSupportingText(text=msg),
                MDDialogButtonContainer(
                    MDButton(
                        MDButtonText(text="OK"),
                        style="text",
                        on_release=lambda *_: self._ai_dialog.dismiss() if self._ai_dialog else None,
                    ),
                ),
            )
            self._ai_dialog.open()

        Clock.schedule_once(on_done, 0)

    def _seed_quizzes_background(self) -> None:
        """Заполняем тесты в фоне"""
        try:
            seeded = seed_quizzes_if_needed(self.courses_db)

            def notify(_dt):
                self.toast("Тесты подготовлены" if seeded else "Тесты уже готовы")

            Clock.schedule_once(notify, 0)
        except Exception as e:
            def notify_err(_dt):
                self.toast(f"Ошибка подготовки тестов: {e}")
            Clock.schedule_once(notify_err, 0)


if __name__ == "__main__":
    _early_log("=== __main__ starting ===")
    try:
        _early_log("Creating MoleculeMentorApp...")
        app = MoleculeMentorApp()
        _early_log("MoleculeMentorApp created, calling run()...")
        app.run()
        _early_log("App finished normally")
    except Exception as exc:
        _early_log(f"=== MAIN EXCEPTION: {exc} ===")
        _early_log(traceback.format_exc())
        _log_startup_exception(exc)
        raise
