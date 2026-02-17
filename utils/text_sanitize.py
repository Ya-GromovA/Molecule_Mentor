from __future__ import annotations

import re


_SUBSCRIPT_MAP = str.maketrans({
    "₀": "0",
    "₁": "1",
    "₂": "2",
    "₃": "3",
    "₄": "4",
    "₅": "5",
    "₆": "6",
    "₇": "7",
    "₈": "8",
    "₉": "9",
})


def sanitize_text_for_kivy(text: str) -> str:
    if not text:
        return ""


    text = text.replace("\\[", "").replace("\\]", "")
    text = text.replace("\\(", "").replace("\\)", "")
    text = text.replace("\\rightarrow", "->")
    text = text.replace("\\leftarrow", "<-")
    text = text.replace("\\leftrightarrow", "<->")
    text = text.replace("\\rightleftharpoons", "<->")
    text = text.replace("\\leftrightharpoons", "<->")
    text = re.sub(r"\\text\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\^\{([^}]*)\}", r"^\1", text)
    text = re.sub(r"_\{([^}]*)\}", r"_\1", text)
    text = text.replace("\\", "")


    repl = {
        "σ": "сигма",
        "π": "пи",
        "α": "альфа",
        "β": "бета",
        "γ": "гамма",
        "δ": "дельта",
        "→": "->",
        "←": "<-",
        "↔": "<->",
        "⇌": "<->",
        "≡": "=",
        "≠": "!=",
        "≤": "<=",
        "≥": ">=",
        "±": "+/-",
        "°": " град ",
        "−": "-",
        "–": "-",
        "—": " - ",
        "…": "...",
        "«": '"',
        "»": '"',
        "“": '"',
        "”": '"',
        "’": "'",
        "‘": "'",
        "×": "x",
        "·": "*",
        "•": "*",
    }
    for a, b in repl.items():
        text = text.replace(a, b)


    text = text.translate(_SUBSCRIPT_MAP)


    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)


    allowed = r"\x00-\x7F\u0400-\u04FF\s.,;:!?(){}\"'/\\|+<>=\-\[\]_#"
    text = re.sub(r"[^" + allowed + r"]", "", text)

    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
