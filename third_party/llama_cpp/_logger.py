import sys
import ctypes
import logging
import os

import llama_cpp









GGML_LOG_LEVEL_TO_LOGGING_LEVEL = {
    0: logging.CRITICAL,
    1: logging.INFO,
    2: logging.WARNING,
    3: logging.ERROR,
    4: logging.DEBUG,
    5: logging.DEBUG,
}

logger = logging.getLogger("llama-cpp-python")

_last_log_level = GGML_LOG_LEVEL_TO_LOGGING_LEVEL[0]


def _append_android_llama_log(msg: str) -> None:
    try:
        android_private = os.environ.get("ANDROID_PRIVATE", "")
        if not android_private:
            return
        path = os.path.join(android_private, "llama_load.log")
        with open(path, "a", encoding="utf-8") as f:
            f.write(msg)
    except Exception:
        pass


# typedef void (*ggml_log_callback)(enum ggml_log_level level, const char * text, void * user_data);
@llama_cpp.llama_log_callback
def llama_log_callback(
    level: int,
    text: bytes,
    user_data: ctypes.c_void_p,
):

    global _last_log_level
    log_level = GGML_LOG_LEVEL_TO_LOGGING_LEVEL[level] if level != 5 else _last_log_level
    decoded = text.decode("utf-8", errors="replace")
    _append_android_llama_log(f"[ggml:{level}] {decoded}")
    if logger.level <= GGML_LOG_LEVEL_TO_LOGGING_LEVEL[level]:
        print(decoded, end="", flush=True, file=sys.stderr)
    _last_log_level = log_level


llama_cpp.llama_log_set(llama_log_callback, ctypes.c_void_p(0))


def set_verbose(verbose: bool):
    logger.setLevel(logging.DEBUG if verbose else logging.ERROR)
