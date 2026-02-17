from __future__ import annotations

import os
from ctypes import (
    c_bool,
    c_char_p,
    c_int,
    c_uint8,
    c_float,
    c_void_p,
    POINTER,
    _Pointer,
    Structure,
)
import pathlib
from typing import (
    Union,
    NewType,
    Optional,
    TYPE_CHECKING,
)

import llama_cpp.llama_cpp as llama_cpp

from llama_cpp._ctypes_extensions import (
    load_shared_library,
    ctypes_function_for_shared_library,
)

if TYPE_CHECKING:
    from llama_cpp._ctypes_extensions import (
        CtypesArray,
    )



_libllava_base_name = "llava"
_libllava_override_path = os.environ.get("LLAVA_CPP_LIB")
_libllava_base_path = pathlib.Path(os.path.abspath(os.path.dirname(__file__))) / "lib" if _libllava_override_path is None else pathlib.Path()


_libllava = load_shared_library(_libllava_base_name, _libllava_base_path)

ctypes_function = ctypes_function_for_shared_library(_libllava)







clip_ctx_p = NewType("clip_ctx_p", int)
clip_ctx_p_ctypes = c_void_p






class llava_image_embed(Structure):
    _fields_ = [
        ("embed", POINTER(c_float)),
        ("n_image_pos", c_int),
    ]




@ctypes_function(
    "llava_validate_embed_size",
    [llama_cpp.llama_context_p_ctypes, clip_ctx_p_ctypes],
    c_bool,
)
def llava_validate_embed_size(
    ctx_llama: llama_cpp.llama_context_p, ctx_clip: clip_ctx_p, /
) -> bool:
    ...




@ctypes_function(
    "llava_image_embed_make_with_bytes",
    [clip_ctx_p_ctypes, c_int, POINTER(c_uint8), c_int],
    POINTER(llava_image_embed),
)
def llava_image_embed_make_with_bytes(
    ctx_clip: clip_ctx_p,
    n_threads: Union[c_int, int],
    image_bytes: CtypesArray[c_uint8],
    image_bytes_length: Union[c_int, int],
    /,
) -> "_Pointer[llava_image_embed]":
    ...




@ctypes_function(
    "llava_image_embed_make_with_filename",
    [clip_ctx_p_ctypes, c_int, c_char_p],
    POINTER(llava_image_embed),
)
def llava_image_embed_make_with_filename(
    ctx_clip: clip_ctx_p, n_threads: Union[c_int, int], image_path: bytes, /
) -> "_Pointer[llava_image_embed]":
    ...




@ctypes_function("llava_image_embed_free", [POINTER(llava_image_embed)], None)
def llava_image_embed_free(embed: "_Pointer[llava_image_embed]", /):
    ...




@ctypes_function(
    "llava_eval_image_embed",
    [
        llama_cpp.llama_context_p_ctypes,
        POINTER(llava_image_embed),
        c_int,
        POINTER(c_int),
    ],
    c_bool,
)
def llava_eval_image_embed(
    ctx_llama: llama_cpp.llama_context_p,
    embed: "_Pointer[llava_image_embed]",
    n_batch: Union[c_int, int],
    n_past: "_Pointer[c_int]",
    /,
) -> bool:
    ...









@ctypes_function("clip_model_load", [c_char_p, c_int], clip_ctx_p_ctypes)
def clip_model_load(
    fname: bytes, verbosity: Union[c_int, int], /
) -> Optional[clip_ctx_p]:
    ...




@ctypes_function("clip_free", [clip_ctx_p_ctypes], None)
def clip_free(ctx: clip_ctx_p, /):
    ...

