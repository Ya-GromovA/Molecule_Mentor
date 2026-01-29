# /home/ulyashka_88/molecule-mentor/ai_engine.py
from __future__ import annotations

import json
import os
import re
import socket
import sys
import threading
import time
import ctypes
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
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
    mode: str  # "ONLINE" | "OFFLINE" | "N/A"
    last_switch_ts: float


class AIEngine:
    # движок для работы с ИИ
    # может работать через интернет (HuggingFace) или локально (llama_cpp)
    # метод ask() блокирующий - вызывать только из фонового потока!

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

        # кеш для загруженных фактов (чтобы не качать каждый раз)
        self._retrieval_cache: Dict[str, Tuple[float, str, list[str]]] = {}
        self._retrieval_cache_ttl_sec = int(os.environ.get("MM_RETRIEVAL_CACHE_TTL", "86400"))  # 24 часа

        self._stop = False
        self._health_thread = threading.Thread(target=self._health_loop, daemon=True)
        self._health_thread.start()

    # -------- внешние методы --------
    def stop(self) -> None:
        self._stop = True
        # ждём пока фоновый поток завершится
        if self._health_thread and self._health_thread.is_alive():
            self._health_thread.join(timeout=2.0)

    def mode(self) -> str:
        with self._lock:
            return self._mode

    def set_offline_model_path(self, path: str) -> None:
        # устанавливаем путь к оффлайн модели
        # сбрасываем кеш чтобы подгрузилась с нового места
        with self._lock:
            self.offline_model_path = path
            self._llama = None
            self._llama_err = ""

    def diagnose(self) -> Diagnose:
        token = self._read_token()
        hf_exists = bool(token)
        offline_exists = os.path.exists(self.offline_model_path) and os.path.getsize(self.offline_model_path) > 0
        llama_ok = self._try_import_llama()

        with self._lock:
            mode = self._mode
            online_ok = self._online_ok
            online_err = self._online_err
            llama_err = self._llama_err
            last_switch = self._last_switch

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

    # -------- контроль языка --------
    _RE_LATIN_ANY = re.compile(r"[A-Za-z]")
    _RE_FORMULA_TOKEN = re.compile(r"^(?:[A-Z][a-z]?\d*){1,12}[+-]?$")

    # разрешаем органику типа R-COOH, R'-OH
    _RE_ORGANIC_TOKEN = re.compile(r"^(?:R|R'|R')(?:[A-Za-z0-9''+\-()]{0,32})$")

    # заменяем английские слова на русские (расширенный словарь для оффлайн модели)
    FORCED_RU_TERMS = {
        # Общие слова
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
        
        # Химические термины
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
        
        # Биология/общее
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
        
        # Применение
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
    
    # фиксы опечаток которые модель часто делает
    TYPO_FIXES = {
        "спиры": "спирты",
        "спиров": "спиртов",
        "спирам": "спиртам",
        "спирами": "спиртами",
        "спирах": "спиртах",
        "альдегиы": "альдегиды",
        "кетоы": "кетоны",
        "кислоы": "кислоты",
    }

    # -------- промпты для модели --------
    def _system_prompt_ru(self, is_offline: bool = False) -> str:
        base = (
            "Ты — эксперт по химии для школьников 7–11 классов.\n"
            "ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ.\n"
            "Запрещено использовать английские слова, кроме химических формул.\n"
            
            "КРИТИЧЕСКИ ПРАВИЛА:\n"
            "1) Пиши только ВЕРНЫЕ факты из школьного курса химии.\n"
            "2) Если не уверен в ответе — напиши «Я не знаю точного ответа».\n"
            "3) Никогда не выдумывай данные и не давай неверных определений.\n"
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
        
        if is_offline:
            base += (
                "\nВАЖНО: отвечай КРАТКО, 3-5 предложений максимум.\n"
                "Используй ТОЛЬКО русские слова. Никаких английских слов!\n"
                "Пиши простым языком для школьника.\n"
            )
        
        return base

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

    # -------- поиск фактов в интернете --------
    def _is_chem_query(self, text: str) -> bool:
        # проверяем похож ли вопрос на химический
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
        # вытаскиваем термин для поиска
        # например "перечисли спирты" -> "спирты"
        t = (text or "").strip().lower()
        t = re.sub(r"[^\w\s\-ёЁа-яА-Я]", " ", t)
        t = re.sub(r"\s{2,}", " ", t).strip()

        if not t:
            return ""

        # убираем всякие "расскажи", "что такое" и т.д.
        stop_prefixes = (
            "объясни", "расскажи", "что такое", "что значит", "дай определение", "определи",
            "перечисли", "назови", "приведи", "покажи", "как", "почему", "зачем",
            "подробно", "кратко",
        )
        for sp in stop_prefixes:
            if t.startswith(sp + " "):
                t = t[len(sp):].strip()

        # убираем мусорные слова
        stop_words = {
            "пожалуйста", "мне", "про", "о", "об", "это", "такое", "значит",
            "на", "в", "и", "или", "что", "как", "какие", "какой", "в", "для",
            "класс", "курсе", "школьной", "школа", "уроке", "учебный",
        }
        parts = [p for p in t.split() if p and p not in stop_words]
        if not parts:
            return ""

        # берём последние 1-2 слова - там обычно и термин
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
        # качаем краткое описание из википедии
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
        # качаем формулу и IUPAC название из PubChem
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
        # собираем факты из разных источников
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

    # -------- нормализация текста для Kivy --------
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
        # заменяем всякие юникодные символы на обычные
        # потому что в Kivy они показываются квадратиками
        if not text:
            return ""

        # заменяем стрелки и математические символы
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

        # индексы в формулах -> обычные цифры (H₂O -> H2O), степени тоже
        text = text.translate(self._SUBSCRIPT_MAP)
        text = text.translate(self._SUPERSCRIPT_MAP)

        return text

    # -------- обработка ответов --------
    def _needs_russian_rewrite(self, answer: str) -> bool:
        # проверяем что нет английских слов
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

            # разрешаем формулы типа NaOH, H2O
            if self._RE_FORMULA_TOKEN.fullmatch(tok):
                continue

            # разрешаем органику типа R-COOH
            if self._RE_ORGANIC_TOKEN.fullmatch(tok):
                continue

            # разрешаем отдельные обозначения элементов
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

        # сначала and/or как единый токен
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
        
        # Применяем словарь замен
        text = self._force_ru_terms(text)
        
        # Убираем двойные пробелы которые могли появиться
        text = re.sub(r'\s{2,}', ' ', text)
        
        # Убираем пробелы перед знаками препинания
        text = re.sub(r'\s+([.,;:!?)])', r'\1', text)
        
        # Исправляем опечатки
        text = self._fix_typos(text)
        
        return text.strip()
    
    def _fix_typos(self, text: str) -> str:
        # исправляем опечатки типа "спиры"
        if not text:
            return text
        
        for typo, fix in self.TYPO_FIXES.items():
            # регистронезависимая замена с сохранением первой буквы
            pattern = re.compile(re.escape(typo), re.IGNORECASE)
            def replace_match(m):
                matched = m.group(0)
                if matched[0].isupper():
                    return fix.capitalize()
                return fix
            text = pattern.sub(replace_match, text)
        
        return text

    def _fix_cyrillic_confusables(self, text: str) -> str:
        # если внутри слова попалась латиница, меняем на русские буквы
        # например Vензол -> Бензол
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

        # чистим совсем странные символы
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

            # убираем технические символы
            if code < 32 or (0xD800 <= code <= 0xDFFF):
                continue

            cleaned.append(ch)

        text = "".join(cleaned)

        # убираем невидимые символы
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

        # убираем лишние пробелы
        text = re.sub(r"[ \t]{2,}", " ", text).strip()
        
        # выкидываем пустые строки
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)
        
        return text
    
    def _is_answer_quality_good(self, text: str) -> bool:
        # проверяем что ответ не пустой и без мусора
        if not text or len(text.strip()) < 20:
            return False
        
        # если в слове смешаны кириллица и латиница - плохо
        mixed_script_pattern = re.compile(r'[А-Яа-яЁё][A-Za-z]{2,}|[A-Za-z]{2,}[А-Яа-яЁё]')
        if mixed_script_pattern.search(text):
            return False
        
        # ловим грубые ошибки по химии
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

    # -------- основной метод --------
    def ask(self, text: str, history: Optional[list[dict]] = None, timeout_sec: int = 20, verify: bool = True) -> str:
        # главный метод для запроса к ИИ
        history = history or []
        text = (text or "").strip()
        if not text:
            return "Напиши вопрос 🙂"

        m = self.mode()
        is_offline = m == "OFFLINE"

        # если вопрос похож на химический - подтягиваем факты
        retrieved_ctx = ""
        retrieved_sources: list[str] = []
        strict_sources = os.environ.get("MM_STRICT_SOURCES", "0").strip().lower() not in ("0", "false", "no")

        # В оффлайне не тянем источники из интернета
        if not is_offline and self._is_chem_query(text):
            term = self._extract_term_ru(text)
            retrieved_ctx, retrieved_sources = self._build_retrieved_context_ru(term)

            # если в строгом режиме и источников нет - не отвечаем выдумкой
            if strict_sources and not retrieved_ctx:
                return (
                    "Не нашла подтверждённых данных в источниках. "
                    "Уточни термин (например, добавь синоним в скобках) или напиши формулу/контекст.\n"
                    f"Что искала: «{term}»"
                )

        # системный промпт живёт здесь, не в интерфейсе
        base_messages: list[dict] = [{"role": "system", "content": self._system_prompt_ru(is_offline=is_offline)}]
        base_messages.extend(history[-20:])

        # если есть факты - запрещаем придумывать своё
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

        base_messages.append({"role": "user", "content": text})

        def do_call(messages: list[dict]) -> str:
            nonlocal is_offline  # чтобы можно было обновить режим при fallback
            
            if m == "ONLINE":
                try:
                    return self._ask_online(messages, timeout_sec=timeout_sec)
                except Exception as e:
                    with self._lock:
                        self._online_err = str(e)
                        self._online_ok = False
                        # Мгновенно сбрасываем кэш интернета при ошибке запроса
                        self._internet_ok_cached = False
                        self._internet_fail_streak = 1
                    self._switch("OFFLINE")
                    is_offline = True  # обновляем флаг чтобы пропустить rewrite/verify
                    return self._ask_offline(messages)

            if m == "OFFLINE":
                try:
                    return self._ask_offline(messages)
                except Exception as e:
                    return f"Оффлайн-модель временно недоступна: {str(e)[:100]}"

            # если режим N/A - пробуем оффлайн как последний шанс
            is_offline = True
            try:
                return self._ask_offline(messages)
            except Exception:
                return "ИИ сейчас недоступен: нет доступа ни к онлайн, ни к оффлайн модели."

        answer = (do_call(base_messages) or "").strip()

        # если были факты, но ответ пуст - не выдумываем
        if retrieved_ctx and not answer:
            return (
                "Нашла данные в источниках, но не смогла сформировать ответ. "
                "Попробуй задать вопрос короче."
            )

        # В оффлайн режиме пропускаем rewrite и verify чтобы отвечать быстрее
        if not is_offline:
            # переписываем ответ на русском, если проскочила латиница
            for attempt in range(3):
                if self._is_answer_quality_good(answer) and not self._needs_russian_rewrite(answer):
                    break
                
                # если совсем плохо - отдаём фоллбэк
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

            # проверка ответа ещё одной моделью (можно отключить)
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

        # финальная чистка
        answer = self._force_ru_terms(answer)
        answer = self._fix_typos(answer)  # спиры -> спирты и т.п.
        answer = self._sanitize_for_ui(answer)
        answer = self._fix_cyrillic_confusables(answer)

        if retrieved_sources:
            answer = answer.strip() + "\n\nИсточники: " + ", ".join(retrieved_sources)

        return answer

    # -------- внутренние методы --------
    def _switch(self, mode: str) -> None:
        with self._lock:
            if self._mode != mode:
                self._mode = mode
                self._last_switch = time.time()

    def _read_token(self) -> str:
        if self._hf_token:
            return self._hf_token
        if not os.path.exists(self.hf_token_path):
            return ""
        tok = (open(self.hf_token_path, "r", encoding="utf-8").read() or "").strip()
        self._hf_token = tok
        return tok

    def _is_internet_ok(self, timeout: float = 3.0) -> bool:
        """Проверяет доступность интернета реальным HTTP запросом, не только socket."""
        # Сначала быстрая проверка socket
        try:
            with socket.create_connection(("router.huggingface.co", 443), timeout=1.5):
                pass
        except OSError:
            return False
        
        # Затем реальный HTTP HEAD запрос чтобы убедиться что трафик проходит
        try:
            r = self._http.head(
                "https://huggingface.co/api/whoami-v2",
                timeout=timeout,
                allow_redirects=False,
            )
            # Любой ответ (даже 401) означает что интернет работает
            return r.status_code < 500
        except Exception:
            return False

    def _find_llama_lib_dir(self) -> str:
        """Ищет директорию с библиотекой libllama.so"""
        android_private = os.environ.get("ANDROID_PRIVATE", "")
        project_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(project_dir, os.pardir))
        
        potential_paths = []
        
        if android_private:
            # Шаг 1: Пробуем получить путь через jnius (nativeLibraryDir)
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
            
            # Шаг 2: extracted libs из files/native_libs
            files_dir = os.path.dirname(android_private)
            potential_paths.append(os.path.join(files_dir, "native_libs"))
            
            # Шаг 3: Fallback paths
            data_dir = os.path.dirname(files_dir)
            potential_paths.extend([
                os.path.join(data_dir, "lib"),
                os.path.join(data_dir, "lib", "arm64"),
            ])
        else:
            # Desktop: используем assets/llama
            potential_paths.append(os.path.join(project_root, "assets", "llama"))
        
        # Также проверяем LD_LIBRARY_PATH
        ld_path = os.environ.get("LD_LIBRARY_PATH", "")
        if ld_path:
            potential_paths.extend(ld_path.split(":"))
        
        # Ищем libllama.so
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
            # llama_cpp читает LLAMA_CPP_LIB_PATH (директория)
            os.environ["LLAMA_CPP_LIB_PATH"] = llama_dir
            os.environ["LLAMA_CPP_LIB"] = lib_path
            existing = os.environ.get("LD_LIBRARY_PATH", "")
            if llama_dir not in existing.split(":" if existing else ""):
                os.environ["LD_LIBRARY_PATH"] = (llama_dir + ":" + existing).strip(":")

            for dep in ("libomp.so", "libggml-base.so", "libggml-cpu.so", "libggml.so"):
                dep_path = os.path.join(llama_dir, dep)
                if os.path.exists(dep_path):
                    try:
                        ctypes.CDLL(dep_path, mode=ctypes.RTLD_GLOBAL)
                    except Exception:
                        pass

    def _try_import_llama(self) -> bool:
        # Очищаем кеш импорта llama_cpp чтобы переменные окружения применились
        for mod_name in list(sys.modules.keys()):
            if "llama_cpp" in mod_name:
                del sys.modules[mod_name]
        
        try:
            import llama_cpp  # noqa: F401
            return True
        except Exception as e1:
            # Сохраняем первую ошибку для диагностики
            first_err = str(e1)
            # попытка восстановить пути на Android
            try:
                self._ensure_android_llama_paths()
                # Очищаем кеш снова после настройки путей
                for mod_name in list(sys.modules.keys()):
                    if "llama_cpp" in mod_name:
                        del sys.modules[mod_name]
                import llama_cpp  # noqa: F401
                return True
            except Exception as e2:
                # Сохраняем финальную ошибку
                with self._lock:
                    self._llama_err = f"1st: {first_err[:100]}; 2nd: {str(e2)[:100]}"
                return False

    def _ensure_llama(self):
        with self._lock:
            if self._llama is not None:
                return self._llama

        try:
            from llama_cpp import Llama  # type: ignore

            # Используем меньше потоков на мобильных устройствах для стабильности
            cpu_count = os.cpu_count() or 4
            default_threads = min(4, cpu_count)  # не более 4 потоков
            
            llm = Llama(
                model_path=self.offline_model_path,
                n_ctx=int(os.environ.get("LLAMA_N_CTX", "1024")),  # уменьшено с 2048
                n_threads=int(os.environ.get("LLAMA_THREADS", str(default_threads))),
                n_gpu_layers=int(os.environ.get("LLAMA_GPU_LAYERS", "0")),
                verbose=False,
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
        try:
            llm = self._ensure_llama()
        except Exception as e:
            err_msg = str(e)
            if "llama_cpp" in err_msg.lower() or "import" in err_msg.lower():
                return "Оффлайн-модель недоступна: не удалось загрузить библиотеку llama_cpp."
            if "model" in err_msg.lower() or "path" in err_msg.lower() or "file" in err_msg.lower():
                return "Оффлайн-модель не найдена. Пожалуйста, скачайте модель в настройках."
            return f"Ошибка загрузки оффлайн-модели: {err_msg[:100]}"
        
        try:
            res = llm.create_chat_completion(
                messages=messages,
                temperature=0.3,  # чуть выше для более естественного русского
                top_p=0.9,
                max_tokens=400,  # уменьшено с 768 для скорости
            )
            answer = (res["choices"][0]["message"]["content"] or "").strip()
            # Постобработка: заменяем английские слова на русские
            answer = self._translate_english_words(answer)
            return answer
        except Exception as e:
            return f"Ошибка генерации ответа оффлайн-модели: {str(e)[:100]}"

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
        payload = {
            "model": os.environ.get("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct"),
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 800,
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
        # следим за интернетом и моделью, чтобы переключать режим
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
                    # быстро переключаемся если интернета нет
                    if self._internet_fail_streak >= 1:
                        self._internet_ok_cached = False

                internet = self._internet_ok_cached

                offline_ok = (
                    os.path.exists(self.offline_model_path)
                    and os.path.getsize(self.offline_model_path) > 0
                    and self._try_import_llama()
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

            time.sleep(5.0)  # проверяем часто чтобы быстро переключаться
