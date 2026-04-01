
from __future__ import annotations

import json
import os
import re
import socket
import sys
import threading
import time
import ctypes
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, Callable
from urllib.parse import quote

import requests


@dataclass
class Diagnose:
    hf_token_exists: bool
    hf_token_len: int
    online_reachable: bool
    online_last_error: str
    offline_model_exists: bool
    llama_import_ok: bool
    llama_last_error: str
    mode: str
    last_switch_ts: float


class AIEngine:
    OFFLINE_CHEM_DEFS_RU = {
        "химия": (
            "Химия — это наука о веществах: их составе, строении, свойствах и превращениях. "
            "Она изучает, из чего состоят вещества и как они реагируют друг с другом."
        ),
        "бензол": (
            "Бензол — ароматический углеводород с формулой C6H6. "
            "Это бесцветная жидкость с характерным запахом, токсичная; используется как сырьё в химической промышленности."
        ),
        "аспирин": (
            "Аспирин — это ацетилсалициловая кислота, формула C9H8O4. "
            "Применяется как жаропонижающее, обезболивающее и противовоспалительное средство."
        ),
        "вода": "Вода — химическое вещество с формулой H2O, универсальный растворитель и необходимая среда для жизни.",
        "кислота": (
            "Кислоты — это вещества, которые в водном растворе отдают ионы водорода (H+). "
            "Примеры: HCl, H2SO4, HNO3."
        ),
        "основание": (
            "Основания — это вещества, которые в растворе дают гидроксид-ионы OH-. "
            "Примеры: NaOH, KOH, Ca(OH)2."
        ),
        "соль": (
            "Соли — это ионные соединения, обычно продукты реакции кислоты и основания. "
            "Пример: NaCl."
        ),
        "спирт": (
            "Спирт — это органическое соединение, содержащее гидроксильную группу -OH, "
            "связанную с углеводородным радикалом. Общая формула одноатомных предельных спиртов: CnH2n+1OH (или R-OH). "
            "Примеры: метанол CH3OH, этанол C2H5OH."
        ),
        "спирты": (
            "Спирты — это класс органических веществ с гидроксильной группой -OH. "
            "Общая формула одноатомных предельных спиртов: CnH2n+1OH (или R-OH). "
            "Примеры: CH3OH, C2H5OH."
        ),
    }

    CHEM_REFERENCE_FILE = "data/ai/chem_reference.json"

    @staticmethod
    def _log_llama_runtime(msg: str) -> None:
        try:
            android_private = os.environ.get("ANDROID_PRIVATE", "")
            if android_private:
                log_path = os.path.join(android_private, "llama_load.log")
            else:
                log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "llama_load.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[AIEngine] {msg}\n")
        except Exception:
            pass




    def __init__(self, hf_token_path: str, offline_model_path: str):
        self.hf_token_path = hf_token_path
        self.offline_model_path = offline_model_path

        self._lock = threading.RLock()
        self._http = requests.Session()
        self._mode = "N/A"
        self._last_switch = 0.0

        self._hf_token: Optional[str] = None
        self._llama = None
        self._llama_err = ""
        self._online_err = ""
        self._online_ok = False
        self._mode_change_cb: Optional[Callable[[str], None]] = None


        self._retrieval_cache: Dict[str, Tuple[float, str, list[str]]] = {}
        self._retrieval_cache_ttl_sec = int(os.environ.get("MM_RETRIEVAL_CACHE_TTL", "86400"))
        self._local_chem_snippets = self._load_local_chem_snippets()
        self._chem_reference, self._known_nonexistent_terms = self._load_chem_reference_data()
        self._chem_ref_index = self._build_chem_ref_index()

        self._stop = False
        self._health_thread = threading.Thread(target=self._health_loop, daemon=True)
        self._health_thread.start()

    def _load_chem_reference_data(self) -> Tuple[Dict[str, Dict[str, Any]], set[str]]:
        ref: Dict[str, Dict[str, Any]] = {}
        nonexistent: set[str] = set()
        try:
            root = Path(__file__).resolve().parents[1]
            p = root / self.CHEM_REFERENCE_FILE
            if not p.exists():
                return ref, nonexistent

            data = json.loads(p.read_text(encoding="utf-8"))
            terms = data.get("terms", {}) if isinstance(data, dict) else {}
            for k, v in (terms.items() if isinstance(terms, dict) else []):
                key = self._normalize_term_key(str(k))
                if not key or not isinstance(v, dict):
                    continue
                ref[key] = {
                    "formula": str(v.get("formula", "")).strip(),
                    "class": str(v.get("class", "")).strip(),
                    "definition": str(v.get("definition", "")).strip(),
                    "examples": [str(x).strip() for x in (v.get("examples", []) or []) if str(x).strip()],
                    "aliases": [str(x).strip() for x in (v.get("aliases", []) or []) if str(x).strip()],
                }

            raw_non = data.get("nonexistent_terms", []) if isinstance(data, dict) else []
            for t in (raw_non or []):
                n = self._normalize_term_key(str(t))
                if n:
                    nonexistent.add(n)
        except Exception:
            return {}, set()

        return ref, nonexistent

    def _build_chem_ref_index(self) -> Dict[str, str]:
        idx: Dict[str, str] = {}

        def _variants_for(term: str) -> set[str]:
            out = {term}
            # Простейшие русские словоформы (вопросы часто в родительном падеже:
            # "формула магния", "свойства кальция").
            if " " in term:
                return out
            if term.endswith("ий") and len(term) > 3:
                stem = term[:-2]
                out.update({stem + "ия", stem + "ию", stem + "ием", stem + "ии"})
            if term.endswith("й") and len(term) > 2:
                stem = term[:-1]
                out.update({stem + "я", stem + "ю", stem + "ем", stem + "е"})
            if term.endswith("а") and len(term) > 2:
                stem = term[:-1]
                out.update({stem + "ы", stem + "е", stem + "у", stem + "ой"})
            return out

        for canon, item in self._chem_reference.items():
            c = self._normalize_term_key(canon)
            if c:
                for v in _variants_for(c):
                    idx[v] = canon
            for a in item.get("aliases", []) or []:
                an = self._normalize_term_key(str(a))
                if an:
                    for v in _variants_for(an):
                        idx[v] = canon
        return idx


    def stop(self) -> None:
        self._stop = True

        if self._health_thread and self._health_thread.is_alive():
            self._health_thread.join(timeout=2.0)

    def set_mode_change_callback(self, callback: Optional[Callable[[str], None]]) -> None:
        with self._lock:
            self._mode_change_cb = callback

    def mode(self) -> str:
        with self._lock:
            return self._mode

    def set_offline_model_path(self, path: str) -> None:


        with self._lock:
            self.offline_model_path = path
            self._llama = None
            self._llama_err = ""

    def diagnose(self) -> Diagnose:
        token = self._read_token()
        hf_exists = bool(token)
        offline_exists = os.path.exists(self.offline_model_path) and os.path.getsize(self.offline_model_path) > 0

        # Живая проверка для индикатора в UI: обновляем режим сразу,
        # не дожидаясь следующего цикла фонового health-loop.
        live_internet = self._is_internet_ok(
            timeout=0.55,
            hosts=[("1.1.1.1", 53), ("router.huggingface.co", 443)],
        )

        with self._lock:
            self._online_ok = bool(live_internet and hf_exists)
            self._online_err = "" if live_internet else "internet unavailable"

            if self._online_ok:
                self._switch("ONLINE")
            elif offline_exists:
                self._switch("OFFLINE")
            else:
                self._switch("N/A")

            mode = self._mode
            online_ok = self._online_ok
            online_err = self._online_err
            llama_err = self._llama_err
            last_switch = self._last_switch
            llama_loaded = self._llama is not None

        # Не триггерим импорт llama_cpp в диагностике/статусе,
        # чтобы не ловить нативные падения на некоторых устройствах.
        llama_ok = bool(llama_loaded) or (offline_exists and not bool(llama_err))

        return Diagnose(
            hf_token_exists=hf_exists,
            hf_token_len=len(token) if token else 0,
            online_reachable=online_ok,
            online_last_error=online_err or "",
            offline_model_exists=offline_exists,
            llama_import_ok=llama_ok,
            llama_last_error=llama_err or "",
            mode=mode,
            last_switch_ts=last_switch,
        )


    _RE_LATIN_ANY = re.compile(r"[A-Za-z]")
    _RE_FORMULA_TOKEN = re.compile(r"^(?:[A-Z][a-z]?\d*){1,12}[+-]?$")


    _RE_ORGANIC_TOKEN = re.compile(r"^(?:R|R'|R')(?:[A-Za-z0-9''+\-()]{0,32})$")


    FORCED_RU_TERMS = {

        "and/or": "и/или",
        "and": "и",
        "or": "или",
        "the": "",
        "a": "",
        "an": "",
        "is": "это",
        "are": "являются",
        "it": "это",
        "its": "его",
        "this": "это",
        "that": "это",
        "which": "который",
        "where": "где",
        "when": "когда",
        "how": "как",
        "what": "что",
        "many": "многих",
        "other": "другой",
        "others": "другие",
        "some": "некоторые",
        "such": "такие",
        "as": "как",
        "with": "с",
        "without": "без",
        "for": "для",
        "from": "из",
        "in": "в",
        "on": "на",
        "to": "к",
        "of": "",
        "by": "",
        "also": "также",
        "very": "очень",
        "more": "более",
        "most": "наиболее",
        "less": "менее",
        "much": "много",
        "can": "может",
        "may": "может",
        "will": "будет",
        "would": "будет",
        "could": "мог бы",
        "should": "должен",
        "must": "должен",
        "have": "имеют",
        "has": "имеет",
        "had": "имел",
        "do": "",
        "does": "",
        "did": "",
        "not": "не",
        "but": "но",
        "if": "если",
        "then": "тогда",
        "so": "так",
        "because": "потому что",
        "however": "однако",
        "therefore": "поэтому",
        "example": "пример",
        "examples": "примеры",
        "important": "важный",
        "main": "главный",
        "basic": "основной",
        "different": "различный",
        "various": "различные",
        "common": "общий",
        "specific": "конкретный",
        "general": "общий",
        "special": "особый",
        "new": "новый",
        "old": "старый",
        "large": "большой",
        "small": "маленький",
        "high": "высокий",
        "low": "низкий",
        "first": "первый",
        "second": "второй",
        "third": "третий",
        "last": "последний",
        "next": "следующий",
        "only": "только",
        "same": "тот же",
        "each": "каждый",
        "every": "каждый",
        "all": "все",
        "both": "оба",
        "any": "любой",
        "no": "нет",
        "yes": "да",


        "dissolveable": "растворимый",
        "dissolvable": "растворимый",
        "miscible": "смешивающийся",
        "immiscible": "несмешивающийся",
        "texture": "структура",
        "solvent": "растворитель",
        "compound": "соединение",
        "compounds": "соединения",
        "substance": "вещество",
        "substances": "вещества",
        "properties": "свойства",
        "alcohol": "спирт",
        "alcohols": "спирты",
        "spirit": "спирт",
        "spirits": "спирты",
        "spirt": "спирт",
        "cpirt": "спирт",
        "property": "свойство",
        "mixture": "смесь",
        "mixtures": "смеси",
        "solution": "раствор",
        "solutions": "растворы",
        "aqueous": "водный",
        "ionic": "ионный",
        "covalent": "ковалентный",
        "molecular": "молекулярный",
        "atom": "атом",
        "atoms": "атомы",
        "molecule": "молекула",
        "molecules": "молекулы",
        "element": "элемент",
        "elements": "элементы",
        "reaction": "реакция",
        "reactions": "реакции",
        "chemical": "химический",
        "organic": "органический",
        "inorganic": "неорганический",
        "acid": "кислота",
        "acids": "кислоты",
        "base": "основание",
        "bases": "основания",
        "salt": "соль",
        "salts": "соли",
        "water": "вода",
        "oxygen": "кислород",
        "hydrogen": "водород",
        "carbon": "углерод",
        "nitrogen": "азот",
        "energy": "энергия",
        "temperature": "температура",
        "pressure": "давление",
        "concentration": "концентрация",
        "mass": "масса",
        "volume": "объём",
        "density": "плотность",
        "structure": "структура",
        "formula": "формула",
        "formulas": "формулы",
        "bond": "связь",
        "bonds": "связи",
        "electron": "электрон",
        "electrons": "электроны",
        "proton": "протон",
        "protons": "протоны",
        "neutron": "нейтрон",
        "neutrons": "нейтроны",
        "nucleus": "ядро",
        "ion": "ион",
        "ions": "ионы",
        "positive": "положительный",
        "negative": "отрицательный",
        "neutral": "нейтральный",
        "polar": "полярный",
        "nonpolar": "неполярный",


        "living": "живых",
        "organisms": "организмов",
        "organism": "организм",
        "biological": "биологических",
        "processes": "процессов",
        "process": "процесс",
        "cell": "клетка",
        "cells": "клетки",
        "life": "жизнь",
        "nature": "природа",
        "natural": "природный",
        "environment": "окружающая среда",
        "body": "тело",
        "human": "человеческий",
        "plant": "растение",
        "plants": "растения",
        "animal": "животное",
        "animals": "животные",
        "food": "пища",
        "health": "здоровье",


        "used": "используется",
        "use": "использование",
        "uses": "использует",
        "using": "используя",
        "application": "применение",
        "applications": "применения",
        "industry": "промышленность",
        "industrial": "промышленный",
        "production": "производство",
        "medicine": "медицина",
        "medical": "медицинский",
        "technology": "технология",
        "material": "материал",
        "materials": "материалы",
        "irrigation": "орошения",
        "foods": "продуктов",
        "quickly": "быстро",
        "bloodstream": "кровоток",
        "transported": "транспортируется",
        "converted": "преобразуется",
        "enters": "попадает",
        "think": "думать",
        "feel": "чувствовать",
        "move": "двигаться",
        "moves": "движется",
        "source": "источник",
        "sources": "источники",
        "level": "уровень",
        "levels": "уровни",
        "treatment": "лечение",
        "disease": "болезнь",
        "diseases": "болезни",
        "sugar": "сахар",
        "sugars": "сахара",
        "simple": "простой",
        "complex": "сложный",
        "type": "тип",
        "types": "типы",
        "form": "форма",
        "forms": "формы",
        "group": "группа",
        "groups": "группы",
        "class": "класс",
        "name": "название",
        "names": "названия",
        "called": "называется",
        "known": "известный",
        "found": "найден",
        "contains": "содержит",
        "contain": "содержат",
        "consists": "состоит",
        "include": "включают",
        "includes": "включает",
        "including": "включая",
        "exist": "существует",
        "exists": "существуют",
        "formed": "образуется",
        "produced": "производится",
        "occurs": "происходит",
        "takes": "занимает",
        "place": "место",
        "part": "часть",
        "parts": "части",
        "role": "роль",
        "plays": "играет",
        "way": "способ",
        "ways": "способы",
        "method": "метод",
        "methods": "методы",
        "result": "результат",
        "results": "результаты",
        "effect": "эффект",
        "effects": "эффекты",
        "cause": "причина",
        "causes": "причины",
        "reason": "причина",
        "reasons": "причины",
        "factor": "фактор",
        "factors": "факторы",
        "condition": "условие",
        "conditions": "условия",
        "state": "состояние",
        "states": "состояния",
        "change": "изменение",
        "changes": "изменения",
        "increase": "увеличение",
        "decrease": "уменьшение",
        "higher": "выше",
        "lower": "ниже",
        "between": "между",
        "through": "через",
        "into": "в",
        "out": "из",
        "up": "вверх",
        "down": "вниз",
        "over": "над",
        "under": "под",
        "about": "около",
        "around": "около",
        "during": "во время",
        "after": "после",
        "before": "до",
        "while": "пока",
        "until": "до тех пор пока",
        "since": "с тех пор как",
        "although": "хотя",
        "though": "хотя",
        "even": "даже",
        "just": "просто",
        "still": "всё ещё",
        "already": "уже",
        "always": "всегда",
        "never": "никогда",
        "often": "часто",
        "sometimes": "иногда",
        "usually": "обычно",
        "normally": "обычно",
        "especially": "особенно",
        "mainly": "в основном",
        "mostly": "в основном",
        "generally": "обычно",
        "typically": "типично",
        "directly": "напрямую",
        "completely": "полностью",
        "easily": "легко",
        "slowly": "медленно",
        "rapidly": "быстро",
        "immediately": "немедленно",
        "finally": "наконец",
        "together": "вместе",
        "separately": "отдельно",
        "properly": "правильно",
        "exactly": "точно",
        "approximately": "приблизительно",
    }


    TYPO_FIXES = {
        "cpirt": "спирт",
        "spirt": "спирт",
        "спиры": "спирты",
        "спиров": "спиртов",
        "спирам": "спиртам",
        "спирами": "спиртами",
        "спирах": "спиртах",
        "альдегиы": "альдегиды",
        "кетоы": "кетоны",
        "кислоы": "кислоты",
    }


    def _system_prompt_ru(self, is_offline: bool = False) -> str:
        if is_offline:
            return (
                "Ты — помощник по химии для школьников 7-11 классов. "
                "Отвечай только на русском языке, кратко и по делу. "
                "Отвечай строго на ТЕКУЩИЙ вопрос, не повторяй предыдущие ответы. "
                "Давай полезный ответ: определение, формула (если уместно), 1-2 примера и одно свойство/применение. "
                "Не выдумывай факты. Если в деталях не уверен, всё равно дай базовый корректный ответ, "
                "а в конце коротко отметь, что некоторые детали могут быть неточны."
            )

        base = (
            "Ты — эксперт по химии для школьников 7–11 классов.\n"
            "ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ.\n"
            "Запрещено использовать английские слова, кроме химических формул.\n"

            "КРИТИЧЕСКИ ПРАВИЛА:\n"
            "1) Пиши только ВЕРНЫЕ факты из школьного курса химии.\n"
            "2) Если не уверен в ответе — напиши «Я не знаю точного ответа».\n"
            "3) Никогда не выдумывай данные и не давай неверных определений.\n"
            "3.1) Не подставляй другие вещества и чужие формулы, если их нет в вопросе.\n"
            "3.2) Если написал «Я не знаю точного ответа» — остановись и больше ничего не добавляй.\n"
            "4) Латинские буквы ТОЛЬКО в формулах: H2O, CO2, NaOH, CH3OH, C2H5OH, R-COOH.\n"
            "5) Символы: →, <->, +, -, =, цифры — разрешены в формулах.\n"
            "6) Не используй спецсимволы Unicode (↑, ↓, ∞, ± и т.д.) — замени их текстом.\n"

            "ВАЖНЫЕ ХИМИЧЕСКИЕ ФАКТЫ:\n"
            "- Спирты — это производные углеводородов, в которых один атом водорода замещён гидроксильной группой -OH.\n"
            "- Спирты НЕ ЯВЛЯЮТСЯ производными карбоновых кислот.\n"
            "- Общая формула спиртов: CnH2n+1OH или R-OH.\n"

            "СТРУКТУРА ОТВЕТА:\n"
            "1) Определение (что это).\n"
            "2) Формула (если есть).\n"
            "3) Примеры (3-6 штук).\n"
            "4) Свойства и применение.\n"

            "ВАЖНО: ответ должен быть чистым русским текстом без ошибок и странных символов.\n"
        )

        return base

    @staticmethod
    def _trim_if_uncertain(answer: str) -> str:
        a = (answer or "").strip()
        low = a.lower()
        if not a:
            return a

        # Не обрезаем полезный ответ до одной фразы слишком агрессивно.
        # Сводим к "не знаю" только если это и так почти весь ответ.
        uncertainty_hits = (
            "я не знаю" in low
            or "не знаю точного" in low
            or "не уверен" in low
            or "затрудняюсь ответить" in low
        )
        if uncertainty_hits and len(a) < 90:
            return "Я не знаю точного ответа."
        return a

    @staticmethod
    def _guard_unrelated(question: str, answer: str) -> str:
        q = (question or "").lower()
        a = (answer or "").lower()
        if "кофеин" in a and "кофеин" not in q:
            return "Я не знаю точного ответа."
        return answer

    @staticmethod
    def _guard_nonexistent_formula_mix(question: str, answer: str) -> str:
        a = (answer or "")
        al = a.lower()
        says_nonexistent = any(x in al for x in ("не существует", "несуществ", "неизвестно", "нет такого соединения"))
        has_formula = re.search(r"\b(?:[A-Z][a-z]?\d*){2,}[+-]?\b", a) is not None
        if says_nonexistent and has_formula:
            return "Я не знаю точного ответа. Похоже, это соединение не относится к стандартным веществам школьного курса."
        return answer

    def _verifier_prompt_ru(self) -> str:
        return (
            "Ты — строгий научный редактор по школьной химии.\n"
            "Проверь текст на фактические и терминологические ошибки.\n"
            "Если есть ошибки — исправь.\n"
            "Если уверенно исправить нельзя — скажи, каких данных не хватает.\n"
            "Не добавляй новых неподтверждённых фактов.\n"
            "Отвечай только финальным исправленным текстом.\n"
            "Русский язык обязателен, латиница — только в формулах (и R-обозначениях органики).\n"
        )


    def _is_chem_query(self, text: str) -> bool:

        t = (text or "").strip().lower()
        if not t:
            return False
        triggers = (
            "что такое", "что значит", "определи", "дай определение",
            "расскажи", "объясни",
            "перечисли", "назови", "приведи примеры",
            "формула", "общая формула", "структурная формула", "как писать структурные",
            "свойства", "растворимость", "температура кипения", "температура плавления",
            "реакция", "уравнение", "окисление", "восстановление", "этерификация", "гидролиз",
            "класс веществ", "к какому классу",
            "спирты", "альдегиды", "кетоны", "кислоты", "основания", "соли", "углеводы",
        )
        return any(x in t for x in triggers)

    def _extract_term_ru(self, text: str) -> str:


        t = (text or "").strip().lower()
        t = re.sub(r"[^\w\s\-ёЁа-яА-Я]", " ", t)
        t = re.sub(r"\s{2,}", " ", t).strip()

        if not t:
            return ""


        stop_prefixes = (
            "объясни", "расскажи", "что такое", "что значит", "дай определение", "определи",
            "перечисли", "назови", "приведи", "покажи", "как", "почему", "зачем",
            "подробно", "кратко",
        )
        for sp in stop_prefixes:
            if t.startswith(sp + " "):
                t = t[len(sp):].strip()


        stop_words = {
            "пожалуйста", "мне", "про", "о", "об", "это", "такое", "значит",
            "на", "в", "и", "или", "что", "как", "какие", "какой", "в", "для",
            "класс", "курсе", "школьной", "школа", "уроке", "учебный",
        }
        parts = [p for p in t.split() if p and p not in stop_words]
        if not parts:
            return ""


        tail = parts[-2:] if len(parts) > 1 else parts[-1:]
        return " ".join(tail).strip()

    def _http_get_json(self, url: str, timeout_sec: float) -> Optional[Dict[str, Any]]:
        try:
            r = self._http.get(url, timeout=timeout_sec, headers={"User-Agent": "MoleculeMentor/1.0"})
            if r.status_code != 200:
                return None
            return r.json()
        except Exception:
            return None

    def _fetch_wikipedia_ru_summary(self, term: str, timeout_sec: float = 3.0) -> Tuple[str, str]:

        if not term:
            return "", ""
        url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{quote(term)}"
        data = self._http_get_json(url, timeout_sec)
        if not data:
            return "", ""
        title = (data.get("title") or "").strip()
        extract = (data.get("extract") or "").strip()
        return title, extract

    def _fetch_pubchem_basic(self, term: str, timeout_sec: float = 3.0) -> Dict[str, str]:

        if not term:
            return {"formula": "", "iupac": ""}

        url = (
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
            f"{quote(term)}/property/MolecularFormula,IUPACName/JSON"
        )
        data = self._http_get_json(url, timeout_sec)
        if not data:
            return {"formula": "", "iupac": ""}

        props = data.get("PropertyTable", {}).get("Properties", [])
        if not props:
            return {"formula": "", "iupac": ""}

        first = props[0] or {}
        return {
            "formula": (first.get("MolecularFormula") or "").strip(),
            "iupac": (first.get("IUPACName") or "").strip(),
        }

    def _build_retrieved_context_ru(self, term: str) -> Tuple[str, list[str]]:

        if not term:
            return "", []

        key = term.lower().strip()
        now = time.time()
        cached = self._retrieval_cache.get(key)
        if cached:
            ts, ctx, src = cached
            if now - ts < self._retrieval_cache_ttl_sec:
                return ctx, list(src)

        sources: list[str] = []
        chunks: list[str] = []

        title, extract = self._fetch_wikipedia_ru_summary(term)
        if extract:
            sources.append("Wikipedia (ru)")
            chunks.append(f"[Wikipedia] {extract}")

        pub = self._fetch_pubchem_basic(term)
        if pub.get("formula") or pub.get("iupac"):
            sources.append("PubChem")
            line = "[PubChem]"
            if pub.get("formula"):
                line += f" Формула: {pub['formula']}."
            if pub.get("iupac"):
                line += f" IUPAC: {pub['iupac']}."
            chunks.append(line)

        ctx = "\n".join(chunks).strip()
        self._retrieval_cache[key] = (now, ctx, sources)
        return ctx, sources

    def _load_local_chem_snippets(self) -> list[str]:
        snippets: list[str] = []
        try:
            root = Path(__file__).resolve().parents[1]
            p = root / "data" / "courses" / "chem10_adv_outline.json"
            if not p.exists():
                return snippets

            data = json.loads(p.read_text(encoding="utf-8"))
            sections = data.get("sections", []) if isinstance(data, dict) else []

            for sec in sections:
                s_title = (sec.get("title") or "").strip()
                if s_title:
                    snippets.append(s_title)
                for topic in sec.get("topics", []) or []:
                    t_title = (topic.get("title") or "").strip()
                    if t_title:
                        snippets.append(t_title)
        except Exception:
            return []

        out: list[str] = []
        seen = set()
        for s in snippets:
            if s in seen:
                continue
            seen.add(s)
            out.append(s)
        return out

    def _build_local_context_ru(self, query: str, top_n: int = 6) -> str:
        q = (query or "").lower().replace("ё", "е")
        q_tokens = set(re.findall(r"[а-яa-z0-9]{4,}", q))
        if not q_tokens or not self._local_chem_snippets:
            return ""

        scored: list[tuple[int, str]] = []
        for s in self._local_chem_snippets:
            st = s.lower().replace("ё", "е")
            st_tokens = set(re.findall(r"[а-яa-z0-9]{4,}", st))
            if not st_tokens:
                continue
            score = len(q_tokens & st_tokens)
            if score > 0:
                scored.append((score, s))

        if not scored:
            return ""

        scored.sort(key=lambda x: (-x[0], len(x[1])))
        best = [s for _, s in scored[:top_n]]
        return "\n".join(f"- {x}" for x in best)


    _SUBSCRIPT_MAP = str.maketrans({
        "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
        "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
    })
    _SUPERSCRIPT_MAP = str.maketrans({
        "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
        "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
        "⁺": "+", "⁻": "-", "⁼": "=", "⁽": "(", "⁾": ")",
    })

    def _normalize_for_kivy_font(self, text: str) -> str:


        if not text:
            return ""


        replacements = {
            "⇌": "<->",
            "↔": "<->",
            "⟷": "<->",
            "→": "->",
            "⇒": "->",
            "←": "<-",
            "≤": "<=",
            "≥": ">=",
            "×": "x",
            "·": "*",
            "•": "*",
            "—": "-",
            "–": "-",
            "−": "-",
            "“": '"',
            "”": '"',
            "„": '"',
            "«": '"',
            "»": '"',
            "’": "'",
            "‘": "'",
            "…": "...",
        }
        for a, b in replacements.items():
            text = text.replace(a, b)


        text = text.translate(self._SUBSCRIPT_MAP)
        text = text.translate(self._SUPERSCRIPT_MAP)

        return text


    def _needs_russian_rewrite(self, answer: str) -> bool:

        if not answer:
            return False

        if not self._RE_LATIN_ANY.search(answer):
            return False

        for raw in answer.split():
            tok = raw.strip(" \t\r\n.,;:!?()[]{}<>\"'“”«»—–-_/\\|")
            if not tok:
                continue

            if not self._RE_LATIN_ANY.search(tok):
                continue


            if self._RE_FORMULA_TOKEN.fullmatch(tok):
                continue


            if self._RE_ORGANIC_TOKEN.fullmatch(tok):
                continue


            if tok in {
                "pH", "Na", "Cl", "Fe", "Cu", "Zn", "Ag", "Au", "Hg",
                "Pb", "Sn", "Al", "Si", "Ca", "K", "Li", "Mg",
                "H", "O", "C", "N", "S", "P",
            }:
                continue

            return True

        return False

    def _force_ru_terms(self, text: str) -> str:
        if not text:
            return text


        text = re.sub(r"\band/or\b", "и/или", text, flags=re.IGNORECASE)

        for en, ru in self.FORCED_RU_TERMS.items():
            if en.lower() == "and/or":
                continue
            text = re.sub(rf"\b{re.escape(en)}\b", ru, text, flags=re.IGNORECASE)
        return text

    def _translate_english_words(self, text: str) -> str:
        """Заменяет английские слова на русские в ответе оффлайн модели."""
        if not text:
            return text


        text = self._force_ru_terms(text)


        text = re.sub(r'\s{2,}', ' ', text)


        text = re.sub(r'\s+([.,;:!?)])', r'\1', text)


        text = self._fix_typos(text)

        return text.strip()

    def _fix_typos(self, text: str) -> str:

        if not text:
            return text

        for typo, fix in self.TYPO_FIXES.items():

            pattern = re.compile(re.escape(typo), re.IGNORECASE)
            def replace_match(m):
                matched = m.group(0)
                if matched[0].isupper():
                    return fix.capitalize()
                return fix
            text = pattern.sub(replace_match, text)

        return text

    def _fix_cyrillic_confusables(self, text: str) -> str:


        if not text:
            return ""

        conf = str.maketrans({
            "A": "А", "a": "а",
            "B": "В", "E": "Е", "e": "е",
            "K": "К", "M": "М", "H": "Н",
            "O": "О", "o": "о",
            "P": "Р", "p": "р",
            "C": "С", "c": "с",
            "T": "Т", "X": "Х", "x": "х",
            "V": "В", "v": "в",
            "Y": "У", "y": "у",
            "I": "І", "i": "і",
        })

        text = re.sub(
            r"(?<=[А-Яа-яЁё])[A-Za-z](?=[А-Яа-яЁё])",
            lambda m: m.group(0).translate(conf),
            text,
        )
        text = re.sub(
            r"[A-Za-z](?=[А-Яа-яЁё])",
            lambda m: m.group(0).translate(conf),
            text,
        )
        text = re.sub(
            r"(?<=[А-Яа-яЁё])[A-Za-z]",
            lambda m: m.group(0).translate(conf),
            text,
        )

        # Если слово смешанное (кириллица+латиница), доп. транслитерируем
        # оставшиеся латинские буквы в кириллицу. Это чинит кейсы типа
        # "formyла" -> "формула".
        translit_map = {
            "a": "а", "b": "б", "c": "с", "d": "д", "e": "е", "f": "ф",
            "g": "г", "h": "х", "i": "и", "j": "й", "k": "к", "l": "л",
            "m": "м", "n": "н", "o": "о", "p": "п", "q": "к", "r": "р",
            "s": "с", "t": "т", "u": "у", "v": "в", "w": "в", "x": "кс",
            "y": "у", "z": "з",
            "A": "А", "B": "Б", "C": "С", "D": "Д", "E": "Е", "F": "Ф",
            "G": "Г", "H": "Х", "I": "И", "J": "Й", "K": "К", "L": "Л",
            "M": "М", "N": "Н", "O": "О", "P": "П", "Q": "К", "R": "Р",
            "S": "С", "T": "Т", "U": "У", "V": "В", "W": "В", "X": "КС",
            "Y": "У", "Z": "З",
        }

        def _fix_mixed_word(m):
            w = m.group(0)
            has_cyr = re.search(r"[А-Яа-яЁё]", w) is not None
            has_lat = re.search(r"[A-Za-z]", w) is not None
            if not (has_cyr and has_lat):
                return w
            if self._RE_FORMULA_TOKEN.fullmatch(w):
                return w
            out = []
            for ch in w:
                out.append(translit_map.get(ch, ch))
            return "".join(out)

        text = re.sub(r"[A-Za-zА-Яа-яЁё]{3,}", _fix_mixed_word, text)


        allowed_chars = r"\x00-\x7F\u0400-\u04FF\s.,;:!?(){}\"'/\\|+<>=\-\[\]_"
        text = re.sub(r"[^" + allowed_chars + r"]", "", text)

        return text

    def _sanitize_for_ui(self, text: str) -> str:
        if not text:
            return ""

        text = self._normalize_for_kivy_font(text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        cleaned = []
        for ch in text:
            code = ord(ch)

            if ch in ("\n", "\t"):
                cleaned.append(ch)
                continue


            if code < 32 or (0xD800 <= code <= 0xDFFF):
                continue

            cleaned.append(ch)

        text = "".join(cleaned)


        text = text.translate(
            {
                0x200B: None,
                0x200C: None,
                0x200D: None,
                0xFEFF: None,
                0x00AD: None,
                0x200E: None,
                0x200F: None,
            }
        )


        text = re.sub(r"[ \t]{2,}", " ", text).strip()


        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)

        return text

    def _is_answer_quality_good(self, text: str) -> bool:

        if not text or len(text.strip()) < 20:
            return False


        mixed_script_pattern = re.compile(r'[А-Яа-яЁё][A-Za-z]{2,}|[A-Za-z]{2,}[А-Яа-яЁё]')
        if mixed_script_pattern.search(text):
            return False


        wrong_statements = [
            r'спирт.*неорганическ',
            r'альдегид.*неорганическ',
            r'кетон.*неорганическ',
            r'кислот.*неорганическ',
        ]
        for pattern in wrong_statements:
            if re.search(pattern, text, re.IGNORECASE):
                return False

        return True

    @staticmethod
    def _normalize_term_key(term: str) -> str:
        t = (term or "").strip().lower().replace("ё", "е")
        t = re.sub(r"[^а-яa-z0-9+\- ]+", " ", t)
        t = re.sub(r"\s{2,}", " ", t).strip()
        return t

    def _extract_reference_key(self, text: str) -> str:
        q = self._normalize_term_key(text)
        if not q:
            return ""

        if q in self._chem_ref_index:
            return self._chem_ref_index[q]

        term = self._normalize_term_key(self._extract_term_ru(text))
        if term in self._chem_ref_index:
            return self._chem_ref_index[term]

        if q.endswith(" это"):
            k = q[:-4].strip()
            if k in self._chem_ref_index:
                return self._chem_ref_index[k]
        if q.startswith("это "):
            k = q[4:].strip()
            if k in self._chem_ref_index:
                return self._chem_ref_index[k]

        parts = q.split()
        if parts:
            tail = " ".join(parts[-2:])
            if tail in self._chem_ref_index:
                return self._chem_ref_index[tail]
            if parts[-1] in self._chem_ref_index:
                return self._chem_ref_index[parts[-1]]

        # Поиск термина как подстроки в вопросе (с приоритетом самой длинной фразы),
        # чтобы корректно ловить формулировки вида:
        # "что такое магний, назови формулу".
        best = ""
        for k in self._chem_ref_index.keys():
            if not k:
                continue
            if len(k) <= len(best):
                continue
            if re.search(rf"(?<![а-яa-z0-9]){re.escape(k)}(?![а-яa-z0-9])", q):
                best = k
        if best:
            return self._chem_ref_index[best]

        return ""

    def _reference_answer_for(self, text: str) -> Optional[str]:
        key = self._extract_reference_key(text)
        if not key:
            return None
        item = self._chem_reference.get(key)
        if not item:
            return None

        definition = str(item.get("definition", "")).strip()
        formula = str(item.get("formula", "")).strip()
        cls = str(item.get("class", "")).strip()
        examples = [str(x).strip() for x in (item.get("examples", []) or []) if str(x).strip()]
        parts: list[str] = []
        if definition:
            parts.append(definition)
        if cls:
            parts.append(f"Класс: {cls}.")
        if formula:
            if re.fullmatch(r"[A-Z][a-z]?", formula):
                parts.append(f"Химический символ: {formula}.")
            else:
                parts.append(f"Формула: {formula}.")
        if examples:
            parts.append("Примеры: " + ", ".join(examples[:2]) + ".")
        out = " ".join(parts).strip()
        return out or None

    def _reference_nonexistent_answer(self, text: str) -> Optional[str]:
        qn = self._normalize_term_key(text)
        if not qn:
            return None
        for term in self._known_nonexistent_terms:
            if term in qn:
                return (
                    f"Термин «{term}» не относится к стандартным веществам школьного курса химии. "
                    "Уточните корректное название вещества или его формулу."
                )
        return None

    def _validate_with_reference(self, question: str, answer: str) -> str:
        ref = self._reference_answer_for(question)
        if not ref:
            missing = self._reference_nonexistent_answer(question)
            if missing:
                return missing
            return answer

        al = (answer or "").lower()
        if any(x in al for x in ("не существует", "несуществ", "нет такого соединения")):
            return ref

        key = self._extract_reference_key(question)
        formula = str(self._chem_reference.get(key, {}).get("formula", "")).strip()
        if formula:
            has_formula_token = re.search(r"\b(?:[A-Z][a-z]?\d*){2,}[+-]?\b", answer or "") is not None
            formula_ok = formula.lower() in (answer or "").lower()
            if has_formula_token and not formula_ok:
                return ref

        return answer

    def _offline_curated_answer(self, text: str) -> Optional[str]:
        ref_answer = self._reference_answer_for(text)
        if ref_answer:
            return ref_answer

        nonexist = self._reference_nonexistent_answer(text)
        if nonexist:
            return nonexist

        q = (text or "").strip()
        if not q:
            return None
        ql = q.lower()
        qn = self._normalize_term_key(q)

        if qn in self.OFFLINE_CHEM_DEFS_RU:
            return self.OFFLINE_CHEM_DEFS_RU[qn]

        if qn.endswith(" это"):
            k = qn[:-4].strip()
            if k in self.OFFLINE_CHEM_DEFS_RU:
                return self.OFFLINE_CHEM_DEFS_RU[k]
        if qn.startswith("это "):
            k = qn[4:].strip()
            if k in self.OFFLINE_CHEM_DEFS_RU:
                return self.OFFLINE_CHEM_DEFS_RU[k]

        triggers = ("что такое ", "что значит ", "дай определение ", "определи ")
        if not any(ql.startswith(t) for t in triggers):
            if len(qn.split()) <= 2 and qn in self.OFFLINE_CHEM_DEFS_RU:
                return self.OFFLINE_CHEM_DEFS_RU[qn]
            return None

        term = self._extract_term_ru(q)
        key = self._normalize_term_key(term)
        if not key:
            return None

        if key in self.OFFLINE_CHEM_DEFS_RU:
            return self.OFFLINE_CHEM_DEFS_RU[key]

        aliases = {
            "бензен": "бензол",
            "ацетилсалициловая кислота": "аспирин",
            "ацетилсалициловая": "аспирин",
            "алкоголь": "спирт",
            "этанол": "спирт",
        }
        alias = aliases.get(key)
        if alias and alias in self.OFFLINE_CHEM_DEFS_RU:
            return self.OFFLINE_CHEM_DEFS_RU[alias]

        return None

    def prewarm_offline(self) -> None:
        """Прогревает оффлайн-модель в фоне, чтобы первый ответ был быстрее."""
        if not os.path.exists(self.offline_model_path):
            return
        try:
            self._ensure_llama()
        except Exception as e:
            with self._lock:
                self._llama_err = str(e)


    def ask(self, text: str, history: Optional[list[dict]] = None, timeout_sec: int = 20, verify: bool = True, max_tokens: int = 0) -> str:


        history = history or []
        text = (text or "").strip()
        if not text:
            return "Напиши вопрос."

        m = self.mode()
        is_offline = m == "OFFLINE"

        # Вопросы про формулу лучше отдавать детерминированно из справочника,
        # чтобы не было фантазий и неверных падежей/чисел.
        if "формул" in self._normalize_term_key(text):
            formula_ref = self._reference_answer_for(text)
            if formula_ref:
                return formula_ref

        if is_offline or m == "N/A":
            quick_ref = self._reference_answer_for(text)
            if quick_ref:
                return quick_ref
            quick_nonexist = self._reference_nonexistent_answer(text)
            if quick_nonexist:
                return quick_nonexist

        self._max_tokens_override = max_tokens


        retrieved_ctx = ""
        local_ctx = ""
        retrieved_sources: list[str] = []
        strict_sources = os.environ.get("MM_STRICT_SOURCES", "0").strip().lower() not in ("0", "false", "no")


        if not is_offline and self._is_chem_query(text):
            term = self._extract_term_ru(text)
            retrieved_ctx, retrieved_sources = self._build_retrieved_context_ru(term)


            if strict_sources and not retrieved_ctx:
                return (
                    "Не нашла подтверждённых данных в источниках. "
                    "Уточни термин (например, добавь синоним в скобках) или напиши формулу/контекст.\n"
                    f"Что искала: «{term}»"
                )

        if is_offline and self._is_chem_query(text):
            local_ctx = self._build_local_context_ru(text)


        base_messages: list[dict] = [{"role": "system", "content": self._system_prompt_ru(is_offline=is_offline)}]
        if is_offline:
            # Для оффлайн-модели не тащим длинную историю: это ухудшает качество
            # и провоцирует повтор прошлого ответа.
            pass
        else:
            base_messages.extend(history[-20:])


        if retrieved_ctx:
            base_messages.append(
                {
                    "role": "system",
                    "content": (
                        "НИЖЕ — ФАКТЫ ИЗ ВНЕШНИХ ИСТОЧНИКОВ.\n"
                        "Отвечай ТОЛЬКО на их основе.\n"
                        "Запрещено добавлять новые факты, которых нет в этих данных.\n"
                        "Если чего-то не хватает — скажи, что данных недостаточно.\n\n"
                        f"{retrieved_ctx}"
                    ),
                }
            )

        if local_ctx:
            base_messages.append(
                {
                    "role": "system",
                    "content": (
                        "НИЖЕ — ЛОКАЛЬНЫЕ УЧЕБНЫЕ ТЕМЫ ПО ХИМИИ. "
                        "Опирайся на них и на школьный курс, не выдумывай факты.\n"
                        f"{local_ctx}"
                    ),
                }
            )

        base_messages.append({"role": "user", "content": text})

        def do_call(messages: list[dict]) -> str:
            nonlocal is_offline

            online_error = None
            offline_error = None
            online_allowed = False


            if m == "ONLINE":
                online_allowed = self._is_internet_ok(timeout=1.2)
            elif m == "N/A":
                online_allowed = self._is_internet_ok(timeout=2.0)

            if m == "ONLINE" and not online_allowed:
                with self._lock:
                    self._online_ok = False
                    self._online_err = "internet unavailable"
                    self._internet_ok_cached = False
                    self._internet_fail_streak = 1
                self._switch("OFFLINE")
                is_offline = True
                quick = self._offline_curated_answer(text)
                if quick:
                    return quick

            if online_allowed:
                try:
                    return self._ask_online(messages, timeout_sec=timeout_sec)
                except Exception as e:
                    online_error = str(e)
                    with self._lock:
                        self._online_err = online_error
                        self._online_ok = False
                        self._internet_ok_cached = False
                        self._internet_fail_streak = 1
                    self._switch("OFFLINE")
                    is_offline = True
                    quick = self._offline_curated_answer(text)
                    if quick:
                        return quick


            if m == "OFFLINE" or is_offline or m == "N/A":
                is_offline = True
                try:
                    return self._ask_offline(messages)
                except Exception as e:
                    offline_error = str(e)


            if online_error and offline_error:
                return f"ИИ недоступен. Онлайн: {online_error[:50]}. Оффлайн: {offline_error[:50]}"
            elif offline_error:
                return f"Оффлайн-модель недоступна: {offline_error[:100]}"
            elif online_error:
                return f"Онлайн ИИ недоступен: {online_error[:100]}"

            return "ИИ сейчас недоступен."

        answer = (do_call(base_messages) or "").strip()


        if retrieved_ctx and not answer:
            return (
                "Нашла данные в источниках, но не смогла сформировать ответ. "
                "Попробуй задать вопрос короче."
            )


        if not is_offline:

            for attempt in range(3):
                if self._is_answer_quality_good(answer) and not self._needs_russian_rewrite(answer):
                    break


                if attempt >= 2 and not self._is_answer_quality_good(answer):
                    answer = "К сожалению, я не смог дать корректный ответ на этот вопрос. Попробуйте переформулировать вопрос или задать другой."
                    break

                rewrite_messages = [
                    {"role": "system", "content": self._system_prompt_ru(is_offline=is_offline)},
                    {
                        "role": "user",
                        "content": (
                            "Перепиши ответ СТРОГО на русском языке.\n"
                            "1) Убери ВСЕ английские слова, кроме химических формул.\n"
                            "2) Не используй странные символы, напиши обычными буквами.\n"
                            "3) Если ответ химически некорректный - напиши честное 'я не знаю'.\n"
                            "4) Химические формулы: H2O, CO2, NaOH, CH3OH, C2H5OH.\n"
                            "5) Сохрани смысл оригинального ответа.\n\n"
                            f"ОРИГИНАЛ:\n{answer}"
                        ),
                    },
                ]
                rewritten = (do_call(rewrite_messages) or "").strip()
                if rewritten and rewritten != answer:
                    answer = rewritten
                else:
                    break


            verify_enabled = (
                verify
                and os.environ.get("MM_AI_VERIFY", "1").strip().lower() not in ("0", "false", "no")
            )
            if verify_enabled and answer:
                verify_messages = [
                    {"role": "system", "content": self._verifier_prompt_ru()},
                    {"role": "user", "content": answer},
                ]
                verified = (do_call(verify_messages) or "").strip()
                if verified:
                    answer = verified


        answer = self._guard_unrelated(text, answer)
        answer = self._guard_nonexistent_formula_mix(text, answer)
        if is_offline:
            answer = self._validate_with_reference(text, answer)
        answer = self._trim_if_uncertain(answer)

        low_answer = (answer or "").lower()
        is_tech_error = (
            low_answer.startswith("оффлайн-модель")
            or low_answer.startswith("ошибка загрузки")
            or low_answer.startswith("ошибка генерации")
            or low_answer.startswith("ии недоступен")
        )

        if not is_tech_error:
            answer = self._force_ru_terms(answer)
            answer = self._fix_typos(answer)

        if is_offline and self._needs_russian_rewrite(answer) and not is_tech_error:
            repaired = self._translate_english_words(answer)
            repaired = self._fix_cyrillic_confusables(repaired)
            if repaired and not self._needs_russian_rewrite(repaired):
                answer = repaired
            else:
                curated = self._offline_curated_answer(text)
                if curated:
                    answer = curated
                elif self._is_answer_quality_good(repaired):
                    answer = repaired
                else:
                    # Не проваливаемся слишком часто в «не знаю»:
                    # возвращаем наиболее полезную очищенную версию,
                    # а отказ даём только если ответ совсем пустой/короткий.
                    cleaned = (repaired or answer or "").strip()
                    if len(cleaned) >= 24:
                        answer = cleaned
                    else:
                        answer = "Не удалось надежно распознать ответ оффлайн-модели. Переформулируйте вопрос короче."

        answer = self._sanitize_for_ui(answer)
        answer = self._fix_cyrillic_confusables(answer)

        if retrieved_sources:
            answer = answer.strip() + "\n\nИсточники: " + ", ".join(retrieved_sources)

        return answer


    def _switch(self, mode: str) -> None:
        callback: Optional[Callable[[str], None]] = None
        changed = False
        with self._lock:
            if self._mode != mode:
                self._mode = mode
                self._last_switch = time.time()
                callback = self._mode_change_cb
                changed = True
        if changed and callback:
            try:
                callback(mode)
            except Exception:
                pass

    def _read_token(self) -> str:
        if self._hf_token:
            return self._hf_token
        if not os.path.exists(self.hf_token_path):
            return ""
        tok = (open(self.hf_token_path, "r", encoding="utf-8").read() or "").strip()
        self._hf_token = tok
        return tok

    def _is_internet_ok(self, timeout: float = 3.0, hosts: Optional[list[tuple[str, int]]] = None) -> bool:
        """Проверяет доступность интернета через socket connection."""

        android_connected = self._android_network_connected()
        if android_connected is False:
            return False

        if hosts is None:
            hosts = [
                ("1.1.1.1", 53),
                ("8.8.8.8", 53),
                ("router.huggingface.co", 443),
                ("huggingface.co", 443),
                ("google.com", 443),
            ]
        for host, port in hosts:
            try:
                with socket.create_connection((host, port), timeout=timeout):
                    return True
            except OSError:
                continue
        return False

    def _android_network_connected(self) -> Optional[bool]:
        """Быстрая проверка наличия активной сети на Android (без DNS)."""
        if "ANDROID_ARGUMENT" not in os.environ and "ANDROID_PRIVATE" not in os.environ:
            return None

        try:
            from jnius import autoclass

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            BuildVersion = autoclass("android.os.Build$VERSION")

            activity = PythonActivity.mActivity
            if activity is None:
                return None

            cm = activity.getSystemService(Context.CONNECTIVITY_SERVICE)
            if cm is None:
                return None

            sdk_int = int(getattr(BuildVersion, "SDK_INT", 0) or 0)
            if sdk_int >= 23:
                NetworkCapabilities = autoclass("android.net.NetworkCapabilities")
                network = cm.getActiveNetwork()
                if network is None:
                    return False

                caps = cm.getNetworkCapabilities(network)
                if caps is None:
                    return False

                has_internet = bool(caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET))
                has_transport = bool(
                    caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)
                    or caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)
                    or caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)
                )
                return has_internet and has_transport

            info = cm.getActiveNetworkInfo()
            return bool(info and info.isConnected())
        except Exception:
            return None

    def _find_llama_lib_dir(self) -> str:
        """Ищет директорию с библиотекой libllama.so"""
        android_private = os.environ.get("ANDROID_PRIVATE", "")
        android_argument = os.environ.get("ANDROID_ARGUMENT", "")
        project_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(project_dir, os.pardir))

        potential_paths = []

        if android_private or android_argument:

            try:
                from jnius import autoclass
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                activity = PythonActivity.mActivity
                if activity:
                    app_info = activity.getApplicationInfo()
                    native_lib_dir = app_info.nativeLibraryDir
                    if native_lib_dir:
                        potential_paths.append(native_lib_dir)
            except Exception:
                pass


            files_dir = os.path.dirname(android_private) if android_private else os.path.dirname(android_argument)
            if files_dir:
                potential_paths.append(os.path.join(files_dir, "native_libs"))


            if files_dir:
                data_dir = os.path.dirname(files_dir)
                potential_paths.extend([
                    os.path.join(data_dir, "lib"),
                    os.path.join(data_dir, "lib", "arm64"),
                    os.path.join(data_dir, "lib", "arm64-v8a"),
                ])
        else:

            potential_paths.append(os.path.join(project_root, "assets", "llama"))


        ld_path = os.environ.get("LD_LIBRARY_PATH", "")
        if ld_path:
            potential_paths.extend(ld_path.split(":"))


        for path in potential_paths:
            if not path or not os.path.isdir(path):
                continue
            lib_path = os.path.join(path, "libllama.so")
            if os.path.exists(lib_path):
                return path

        return ""

    def _ensure_android_llama_paths(self) -> None:
        if "ANDROID_ARGUMENT" not in os.environ and "ANDROID_PRIVATE" not in os.environ:
            return

        project_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(project_dir, os.pardir))
        third_party_dir = os.path.join(project_root, "third_party")
        if third_party_dir not in sys.path:
            sys.path.insert(0, third_party_dir)

        llama_dir = self._find_llama_lib_dir()

        if not llama_dir:
            return

        lib_path = os.path.join(llama_dir, "libllama.so")
        if os.path.exists(lib_path):

            os.environ["LLAMA_CPP_LIB_PATH"] = llama_dir
            os.environ["LLAMA_CPP_LIB"] = lib_path
            existing = os.environ.get("LD_LIBRARY_PATH", "")
            existing_parts = existing.split(":") if existing else []
            if llama_dir not in existing_parts:
                os.environ["LD_LIBRARY_PATH"] = (llama_dir + ":" + existing).strip(":")

            for dep in ("libomp.so", "libggml-base.so", "libggml-cpu.so", "libggml.so"):
                dep_path = os.path.join(llama_dir, dep)
                if os.path.exists(dep_path):
                    try:
                        ctypes.CDLL(dep_path, mode=ctypes.RTLD_GLOBAL)
                    except Exception:
                        pass

    def _try_import_llama(self) -> bool:

        for mod_name in list(sys.modules.keys()):
            if "llama_cpp" in mod_name:
                del sys.modules[mod_name]

        try:
            import llama_cpp
            return True
        except Exception as e1:

            first_err = str(e1)

            try:
                self._ensure_android_llama_paths()

                for mod_name in list(sys.modules.keys()):
                    if "llama_cpp" in mod_name:
                        del sys.modules[mod_name]
                import llama_cpp
                return True
            except Exception as e2:

                with self._lock:
                    self._llama_err = f"1st: {first_err[:100]}; 2nd: {str(e2)[:100]}"
                return False

    def _ensure_llama(self):
        with self._lock:
            if self._llama is not None:
                return self._llama

        try:
            if not self._try_import_llama():
                with self._lock:
                    reason = self._llama_err or "import llama_cpp failed"
                raise ImportError(reason)

            from llama_cpp import Llama


            cpu_count = os.cpu_count() or 4
            default_threads = min(4, cpu_count)

            n_threads = int(os.environ.get("LLAMA_THREADS", str(default_threads)))
            n_gpu_layers = int(os.environ.get("LLAMA_GPU_LAYERS", "0"))
            env_n_ctx = int(os.environ.get("LLAMA_N_CTX", "1024"))
            env_n_batch = int(os.environ.get("LLAMA_N_BATCH", "64"))
            env_n_ubatch = int(os.environ.get("LLAMA_N_UBATCH", str(env_n_batch)))

            # На Android часто не хватает RAM для больших параметров контекста.
            # Пробуем несколько профилей от обычного к экономному.
            attempts = [
                (env_n_ctx, env_n_batch, env_n_ubatch, n_threads, True),
                (256, 16, 16, max(1, min(2, n_threads)), True),
                (128, 8, 8, 1, True),
                (64, 4, 4, 1, True),
                (64, 2, 2, 1, False),
                (32, 1, 1, 1, False),
                (16, 1, 1, 1, False),
            ]

            # Сохраняем порядок и убираем дубликаты.
            seen = set()
            unique_attempts = []
            for a in attempts:
                if a not in seen:
                    seen.add(a)
                    unique_attempts.append(a)

            last_err = None
            llm = None
            for n_ctx, n_batch, n_ubatch, cur_threads, cur_mmap in unique_attempts:
                try:
                    self._log_llama_runtime(
                        f"try Llama(model={self.offline_model_path}, n_ctx={n_ctx}, n_batch={n_batch}, n_ubatch={n_ubatch}, n_threads={cur_threads}, use_mmap={cur_mmap})"
                    )
                    llm = Llama(
                        model_path=self.offline_model_path,
                        n_ctx=int(n_ctx),
                        n_batch=int(n_batch),
                        n_ubatch=int(n_ubatch),
                        n_threads=max(1, int(cur_threads)),
                        n_threads_batch=1,
                        n_gpu_layers=n_gpu_layers,
                        offload_kqv=False,
                        flash_attn=False,
                        use_mmap=bool(cur_mmap),
                        use_mlock=False,
                        numa=False,
                        verbose=False,
                    )
                    self._log_llama_runtime("Llama() init SUCCESS")
                    break
                except Exception as e:
                    self._log_llama_runtime(f"Llama() init FAILED: {e}")
                    last_err = e

            if llm is None:
                raise RuntimeError(
                    f"Не удалось создать llama_context даже в экономном режиме: {last_err}"
                )

            with self._lock:
                self._llama = llm
                self._llama_err = ""
            return llm
        except Exception as e:
            with self._lock:
                self._llama_err = str(e)
            raise

    def _ask_offline(self, messages: list[dict]) -> str:

        question = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                question = (m.get("content") or "").strip()
                break

        curated = self._offline_curated_answer(question)
        if curated:
            return curated

        if not os.path.exists(self.offline_model_path):
            return f"Оффлайн-модель не найдена: {self.offline_model_path}"

        try:
            llm = self._ensure_llama()
        except Exception as e:
            err_msg = str(e)

            with self._lock:
                self._llama_err = err_msg
            if "llama_cpp" in err_msg.lower() or "import" in err_msg.lower():
                return f"Оффлайн-модель недоступна: не удалось загрузить llama_cpp. {err_msg[:80]}"
            if "create llama_context" in err_msg.lower() or "llama_context" in err_msg.lower():
                return (
                    "Оффлайн-модель скачана, но не запускается на этом устройстве. "
                    "Вероятно, не хватает памяти для локального ИИ."
                )
            if "model" in err_msg.lower() or "path" in err_msg.lower() or "file" in err_msg.lower():
                return f"Оффлайн-модель не найдена по пути: {self.offline_model_path}"
            return f"Ошибка загрузки оффлайн-модели: {err_msg[:100]}"

        def _trim_for_offline(src: list[dict], keep_turns: int, compact_system: bool) -> list[dict]:
            if not src:
                return src

            system_msgs = [m for m in src if m.get("role") == "system"]
            convo = [m for m in src if m.get("role") != "system"]

            last_user = ""
            for m in reversed(convo):
                if m.get("role") == "user":
                    last_user = (m.get("content") or "").strip()
                    break

            if keep_turns <= 0:
                q = last_user or ((convo[-1].get("content") if convo else "") or "")
                convo_part = [{"role": "user", "content": q}]
            else:
                keep_count = max(1, keep_turns * 2 + 1)
                convo_part = convo[-keep_count:]

            if compact_system:
                system_part = [{
                    "role": "system",
                    "content": (
                        "Ты помощник по химии. Ответь только на текущий вопрос на русском языке. "
                        "Формат: что это, формула (если есть), 1-2 примера. "
                        "Не повторяй предыдущие ответы."
                    ),
                }]
            else:
                system_part = system_msgs

            return system_part + convo_part

        base_tokens = getattr(self, "_max_tokens_override", 0) or 240
        plans = [
            (_trim_for_offline(messages, 1, True), min(base_tokens, 120)),
            (_trim_for_offline(messages, 0, True), 96),
            (_trim_for_offline(messages, 0, True), 80),
        ]

        last_err = None
        for plan_messages, plan_tokens in plans:
            try:
                res = llm.create_chat_completion(
                    messages=plan_messages,
                    temperature=0.1,
                    top_p=0.85,
                    repeat_penalty=1.12,
                    max_tokens=plan_tokens,
                )
                answer = (res["choices"][0]["message"]["content"] or "").strip()

                if self._needs_russian_rewrite(answer):
                    answer = self._translate_english_words(answer)

                if self._needs_russian_rewrite(answer):
                    curated_fallback = self._offline_curated_answer(question)
                    if curated_fallback:
                        return curated_fallback

                return answer
            except Exception as e:
                last_err = str(e)
                if "exceed context window" not in last_err.lower() and "requested tokens" not in last_err.lower():
                    return f"Ошибка генерации ответа: {last_err[:100]}"

        return "Слишком длинный диалог для оффлайн-модели. Очистите чат и задайте вопрос снова."

    def _ask_online(self, messages: list[dict], timeout_sec: int) -> str:
        tok = self._read_token()
        if not tok:
            raise RuntimeError("HF token missing")

        base = os.environ.get("HF_ROUTER_BASE", "https://router.huggingface.co/v1")
        url = base.rstrip("/") + "/chat/completions"

        headers = {
            "Authorization": f"Bearer {tok}",
            "Content-Type": "application/json",
        }

        tokens = getattr(self, "_max_tokens_override", 0) or 800
        payload = {
            "model": os.environ.get("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct"),
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": tokens,
        }

        r = self._http.post(url, headers=headers, json=payload, timeout=timeout_sec)

        if r.status_code >= 400:
            raise RuntimeError(f"HF error {r.status_code}: {r.text[:300]}")
        data = r.json()
        try:
            return (data["choices"][0]["message"]["content"] or "").strip()
        except Exception:
            return json.dumps(data)[:800]

    def _health_loop(self) -> None:

        while not self._stop:
            if not hasattr(self, "_internet_fail_streak"):
                self._internet_fail_streak = 0
            if not hasattr(self, "_internet_ok_cached"):
                self._internet_ok_cached = False

            try:
                internet_now = self._is_internet_ok()
                token_ok = bool(self._read_token())

                if internet_now:
                    self._internet_fail_streak = 0
                    self._internet_ok_cached = True
                else:
                    self._internet_fail_streak += 1

                    if self._internet_fail_streak >= 1:
                        self._internet_ok_cached = False

                internet = self._internet_ok_cached

                offline_ok = (
                    os.path.exists(self.offline_model_path)
                    and os.path.getsize(self.offline_model_path) > 0
                )

                if internet and token_ok:
                    with self._lock:
                        self._online_ok = True
                        self._online_err = ""
                    self._switch("ONLINE")
                elif offline_ok:
                    with self._lock:
                        self._online_ok = False
                    self._switch("OFFLINE")
                else:
                    with self._lock:
                        self._online_ok = False
                    self._switch("N/A")

            except Exception as e:
                with self._lock:
                    self._online_ok = False
                    self._online_err = str(e)
                self._switch("N/A")

            time.sleep(3.0)
