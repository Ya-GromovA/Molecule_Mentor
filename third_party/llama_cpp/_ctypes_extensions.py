from __future__ import annotations

import ctypes
import functools
import os
import pathlib
import sys
from typing import Any, Callable, List, Optional, TYPE_CHECKING, TypeVar


def _llama_log(msg: str) -> None:
    try:
        android_private = os.environ.get("ANDROID_PRIVATE", "")
        if not android_private:
            return
        path = os.path.join(android_private, "llama_load.log")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[_ctypes_extensions] {msg}\n")
    except Exception:
        pass


def _is_android() -> bool:
    return bool(os.environ.get("ANDROID_PRIVATE") or os.environ.get("ANDROID_ARGUMENT"))


def _android_lib_dirs(base_path: pathlib.Path) -> List[pathlib.Path]:
    out: List[pathlib.Path] = [base_path]

    override = os.environ.get("LLAMA_CPP_LIB_PATH", "")
    if override:
        out.append(pathlib.Path(override))

    ld = os.environ.get("LD_LIBRARY_PATH", "")
    if ld:
        for p in ld.split(":"):
            if p:
                out.append(pathlib.Path(p))

    android_private = os.environ.get("ANDROID_PRIVATE", "")
    if android_private:
        files_dir = pathlib.Path(android_private).parent
        out.append(files_dir / "native_libs")

    uniq: List[pathlib.Path] = []
    seen = set()
    for p in out:
        s = str(p)
        if s in seen:
            continue
        seen.add(s)
        uniq.append(p)
    return uniq


def load_shared_library(lib_base_name: str, base_path: pathlib.Path):
    lib_paths: List[pathlib.Path] = []

    candidates = _android_lib_dirs(base_path) if _is_android() else [base_path]

    if sys.platform.startswith("linux") or sys.platform.startswith("freebsd"):
        for c in candidates:
            lib_paths.append(c / f"lib{lib_base_name}.so")
    elif sys.platform == "darwin":
        for c in candidates:
            lib_paths.append(c / f"lib{lib_base_name}.so")
            lib_paths.append(c / f"lib{lib_base_name}.dylib")
    elif sys.platform == "win32":
        for c in candidates:
            lib_paths.append(c / f"{lib_base_name}.dll")
            lib_paths.append(c / f"lib{lib_base_name}.dll")
    else:
        raise RuntimeError("Unsupported platform")

    if "LLAMA_CPP_LIB" in os.environ:
        p = pathlib.Path(os.environ["LLAMA_CPP_LIB"])
        lib_paths = [p]

    cdll_args = {}
    if sys.platform == "win32" and sys.version_info >= (3, 8):
        os.add_dll_directory(str(base_path))
        cdll_args["winmode"] = ctypes.RTLD_GLOBAL

    if sys.platform.startswith("linux"):
        deps = ["libomp.so", "libggml-base.so", "libggml-cpu.so", "libggml.so"]
        dep_dirs: List[pathlib.Path] = []
        for p in lib_paths:
            dep_dirs.append(p.parent)
        if _is_android():
            dep_dirs.extend(_android_lib_dirs(base_path))

        dep_seen = set()
        for dep in deps:
            for d in dep_dirs:
                key = (str(d), dep)
                if key in dep_seen:
                    continue
                dep_seen.add(key)
                candidate = d / dep
                if candidate.exists():
                    try:
                        ctypes.CDLL(str(candidate), mode=ctypes.RTLD_GLOBAL)
                        _llama_log(f"loaded dep: {candidate}")
                        break
                    except Exception as e:
                        _llama_log(f"failed dep: {candidate}: {e}")

    last_err: Optional[Exception] = None
    for p in lib_paths:
        _llama_log(f"trying lib: {p}")
        if not p.exists():
            continue
        try:
            lib = ctypes.CDLL(str(p), **cdll_args)
            _llama_log(f"loaded lib: {p}")
            return lib
        except Exception as e:
            last_err = e
            _llama_log(f"failed lib: {p}: {e}")

    if last_err is not None:
        raise RuntimeError(f"Failed to load shared library '{lib_base_name}': {last_err}")
    raise FileNotFoundError(f"Shared library with base name '{lib_base_name}' not found")


if TYPE_CHECKING:
    CtypesCData = TypeVar("CtypesCData", bound=ctypes._CData)
    CtypesArray = ctypes.Array[CtypesCData]
    CtypesPointer = ctypes._Pointer[CtypesCData]
    CtypesVoidPointer = ctypes.c_void_p

    class CtypesRef: ...

    CtypesPointerOrRef = CtypesPointer | CtypesRef
    CtypesFuncPointer = ctypes._FuncPointer

F = TypeVar("F", bound=Callable[..., Any])


def ctypes_function_for_shared_library(lib: ctypes.CDLL):
    def ctypes_function(name: str, argtypes: List[Any], restype: Any, enabled: bool = True):
        def decorator(f: F) -> F:
            if enabled:
                try:
                    func = getattr(lib, name)
                except AttributeError:
                    def _missing_symbol(*args, **kwargs):
                        raise RuntimeError(f"Missing llama symbol: {name}")

                    functools.wraps(f)(_missing_symbol)
                    return _missing_symbol  # type: ignore[return-value]
                func.argtypes = argtypes
                func.restype = restype
                functools.wraps(f)(func)
                return func
            return f

        return decorator

    return ctypes_function


def byref(obj, offset=None):
    if offset is None:
        return ctypes.byref(obj)
    return ctypes.byref(obj, offset)
