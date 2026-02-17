
"""KivyMD 2.x MDTextField color hardening.

Проблема: в KivyMD 2.x иногда цвет вводимого текста в `MDTextField` может
"откатываться" к темному из-за внутренних обновлений темы/состояния.

Цель: сделать вводимый текст *всегда* белым (или заданного цвета)
на Desktop и Android, не ломая разметку и не завязываясь на приватные поля.

Подход:
1) выставляем публичные свойства самого MDTextField (если они есть);
2) находим внутри реальный `TextInput` и фиксируем `foreground_color/cursor_color`;
3) повторяем это на событиях `focus/text/parent` (Android-safe).
"""

from __future__ import annotations

from typing import Iterable, Tuple

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.uix.textinput import TextInput

RGBA = Tuple[float, float, float, float]


def _walk_widgets(root) -> Iterable[object]:
    """Безопасный обход дерева виджетов.

    `walk()` есть почти везде, но на всякий случай делаем fallback.
    """
    try:
        for w in root.walk(restrict=True):
            yield w
        return
    except Exception:
        pass


    stack = [root]
    seen = set()
    while stack:
        w = stack.pop()
        wid = id(w)
        if wid in seen:
            continue
        seen.add(wid)
        yield w
        try:
            stack.extend(getattr(w, "children", []) or [])
        except Exception:
            continue


def harden_mdtextfield_colors(
    tf,
    text_rgba: RGBA,
    cursor_rgba: RGBA | None = None,
    selection_text_rgba: RGBA | None = None,
) -> None:
    """Фиксирует цвета вводимого текста в MDTextField.

    Важно: функция "подписывается" на события виджета и будет подправлять цвет
    по мере необходимости.

    Args:
        tf: экземпляр MDTextField.
        text_rgba: цвет вводимого текста (и заодно cursor по умолчанию).
        cursor_rgba: цвет курсора (если не задан — берём text_rgba).
        selection_text_rgba: цвет текста выделения (если нужен).
    """
    cursor_rgba = cursor_rgba or text_rgba

    def apply(*_args):
        try:

            for attr in ("text_color", "foreground_color"):
                if hasattr(tf, attr):
                    try:
                        setattr(tf, attr, list(text_rgba))
                    except Exception:
                        pass
            if hasattr(tf, "cursor_color"):
                try:
                    tf.cursor_color = list(cursor_rgba)
                except Exception:
                    pass
            if selection_text_rgba and hasattr(tf, "selection_text_color"):
                try:
                    tf.selection_text_color = list(selection_text_rgba)
                except Exception:
                    pass


            found = 0
            for w in _walk_widgets(tf):
                if isinstance(w, TextInput):
                    found += 1
                    try:
                        w.foreground_color = list(text_rgba)
                    except Exception:
                        pass
                    try:
                        w.cursor_color = list(cursor_rgba)
                    except Exception:
                        pass
                    if selection_text_rgba is not None:
                        try:
                            w.selection_text_color = list(selection_text_rgba)
                        except Exception:
                            pass

            if found == 0:
                Logger.debug("[MM][TextFieldColors] TextInput not found inside MDTextField yet")
        except Exception as e:
            Logger.debug(f"[MM][TextFieldColors] apply failed: {e}")


    Clock.schedule_once(apply, 0)

    Clock.schedule_once(apply, 0.05)


    try:
        tf.bind(focus=apply)
    except Exception:
        pass
    try:
        tf.bind(text=apply)
    except Exception:
        pass
    try:
        tf.bind(parent=apply)
    except Exception:
        pass
