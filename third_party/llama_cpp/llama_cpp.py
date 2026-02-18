from __future__ import annotations

import os
import ctypes
import pathlib

from typing import (
    Callable,
    Union,
    NewType,
    Optional,
    TYPE_CHECKING,
)

from llama_cpp._ctypes_extensions import (
    load_shared_library,
    byref,
    ctypes_function_for_shared_library,
)

if TYPE_CHECKING:
    from llama_cpp._ctypes_extensions import (
        CtypesCData,
        CtypesArray,
        CtypesPointer,
        CtypesVoidPointer,
        CtypesRef,
        CtypesPointerOrRef,
        CtypesFuncPointer,
    )



_lib_base_name = "llama"
_override_base_path = os.environ.get("LLAMA_CPP_LIB_PATH")
_base_path = pathlib.Path(os.path.abspath(os.path.dirname(__file__))) / "lib" if _override_base_path is None else pathlib.Path(_override_base_path)

_lib = load_shared_library(_lib_base_name, _base_path)

ctypes_function = ctypes_function_for_shared_library(_lib)





































GGML_TYPE_F32 = 0
GGML_TYPE_F16 = 1
GGML_TYPE_Q4_0 = 2
GGML_TYPE_Q4_1 = 3
GGML_TYPE_Q5_0 = 6
GGML_TYPE_Q5_1 = 7
GGML_TYPE_Q8_0 = 8
GGML_TYPE_Q8_1 = 9
GGML_TYPE_Q2_K = 10
GGML_TYPE_Q3_K = 11
GGML_TYPE_Q4_K = 12
GGML_TYPE_Q5_K = 13
GGML_TYPE_Q6_K = 14
GGML_TYPE_Q8_K = 15
GGML_TYPE_IQ2_XXS = 16
GGML_TYPE_IQ2_XS = 17
GGML_TYPE_IQ3_XXS = 18
GGML_TYPE_IQ1_S = 19
GGML_TYPE_IQ4_NL = 20
GGML_TYPE_IQ3_S = 21
GGML_TYPE_IQ2_S = 22
GGML_TYPE_IQ4_XS = 23
GGML_TYPE_I8 = 24
GGML_TYPE_I16 = 25
GGML_TYPE_I32 = 26
GGML_TYPE_I64 = 27
GGML_TYPE_F64 = 28
GGML_TYPE_IQ1_M = 29
GGML_TYPE_COUNT = 30



ggml_backend_sched_eval_callback = ctypes.CFUNCTYPE(
    ctypes.c_bool, ctypes.c_void_p, ctypes.c_bool, ctypes.c_void_p
)





ggml_abort_callback = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p)



_lib.llama_max_devices.argtypes = []
_lib.llama_max_devices.restype = ctypes.c_size_t

LLAMA_MAX_DEVICES = _lib.llama_max_devices()


LLAMA_DEFAULT_SEED = 0xFFFFFFFF


LLAMA_TOKEN_NULL = -1


LLAMA_FILE_MAGIC_GGLA = 0x67676C61


LLAMA_FILE_MAGIC_GGSN = 0x6767736E


LLAMA_FILE_MAGIC_GGSQ = 0x67677371


LLAMA_SESSION_MAGIC = LLAMA_FILE_MAGIC_GGSN

LLAMA_SESSION_VERSION = 9


LLAMA_STATE_SEQ_MAGIC = LLAMA_FILE_MAGIC_GGSQ

LLAMA_STATE_SEQ_VERSION = 2


llama_vocab_p = NewType("llama_vocab_p", int)
llama_vocab_p_ctypes = ctypes.c_void_p


llama_model_p = NewType("llama_model_p", int)
llama_model_p_ctypes = ctypes.c_void_p


llama_context_p = NewType("llama_context_p", int)
llama_context_p_ctypes = ctypes.c_void_p

# typedef struct llama_memory_i * llama_memory_t;
llama_memory_t = NewType("llama_memory_t", int)
llama_memory_t_ctypes = ctypes.c_void_p

# struct llama_kv_cache; (DEPRECATED)
llama_kv_cache_p = NewType("llama_kv_cache_p", int)
llama_kv_cache_p_ctypes = ctypes.c_void_p

llama_memory_t = NewType("llama_memory_t", int)
llama_memory_t_ctypes = ctypes.c_void_p


llama_kv_cache_p = NewType("llama_kv_cache_p", int)
llama_kv_cache_p_ctypes = ctypes.c_void_p


llama_pos = ctypes.c_int32

llama_token = ctypes.c_int32
llama_token_p = ctypes.POINTER(llama_token)

llama_seq_id = ctypes.c_int32











LLAMA_VOCAB_TYPE_NONE = 0
"""For models without vocab"""
LLAMA_VOCAB_TYPE_SPM = 1
"""LLaMA tokenizer based on byte-level BPE with byte fallback"""
LLAMA_VOCAB_TYPE_BPE = 2
"""GPT-2 tokenizer based on byte-level BPE"""
LLAMA_VOCAB_TYPE_WPM = 3
"""BERT tokenizer based on WordPiece"""
LLAMA_VOCAB_TYPE_UGM = 4
"""T5 tokenizer based on Unigram"""
LLAMA_VOCAB_TYPE_RWKV = 5
"""RWKV tokenizer based on greedy tokenization"""
LLAMA_VOCAB_TYPE_PLAMO2 = 6
"""PLaMo-2 tokenizer based on Aho-Corasick with dynamic programming"""










































LLAMA_VOCAB_PRE_TYPE_DEFAULT = 0
LLAMA_VOCAB_PRE_TYPE_LLAMA3 = 1
LLAMA_VOCAB_PRE_TYPE_DEEPSEEK_LLM = 2
LLAMA_VOCAB_PRE_TYPE_DEEPSEEK_CODER = 3
LLAMA_VOCAB_PRE_TYPE_FALCON = 4
LLAMA_VOCAB_PRE_TYPE_MPT = 5
LLAMA_VOCAB_PRE_TYPE_STARCODER = 6
LLAMA_VOCAB_PRE_TYPE_GPT2 = 7
LLAMA_VOCAB_PRE_TYPE_REFACT = 8
LLAMA_VOCAB_PRE_TYPE_COMMAND_R = 9
LLAMA_VOCAB_PRE_TYPE_STABLELM2 = 10
LLAMA_VOCAB_PRE_TYPE_QWEN2 = 11
LLAMA_VOCAB_PRE_TYPE_OLMO = 12
LLAMA_VOCAB_PRE_TYPE_DBRX = 13
LLAMA_VOCAB_PRE_TYPE_SMAUG = 14
LLAMA_VOCAB_PRE_TYPE_PORO = 15
LLAMA_VOCAB_PRE_TYPE_CHATGLM3 = 16
LLAMA_VOCAB_PRE_TYPE_CHATGLM4 = 17
LLAMA_VOCAB_PRE_TYPE_VIKING = 18
LLAMA_VOCAB_PRE_TYPE_JAIS = 19
LLAMA_VOCAB_PRE_TYPE_TEKKEN = 20
LLAMA_VOCAB_PRE_TYPE_SMOLLM = 21
LLAMA_VOCAB_PRE_TYPE_CODESHELL = 22
LLAMA_VOCAB_PRE_TYPE_BLOOM = 23
LLAMA_VOCAB_PRE_TYPE_GPT3_FINNISH = 24
LLAMA_VOCAB_PRE_TYPE_EXAONE = 25
LLAMA_VOCAB_PRE_TYPE_CHAMELEON = 26
LLAMA_VOCAB_PRE_TYPE_MINERVA = 27
LLAMA_VOCAB_PRE_TYPE_DEEPSEEK3_LLM = 28
LLAMA_VOCAB_PRE_TYPE_GPT4O = 29
LLAMA_VOCAB_PRE_TYPE_SUPERBPE = 30
LLAMA_VOCAB_PRE_TYPE_TRILLION = 31
LLAMA_VOCAB_PRE_TYPE_BAILINGMOE = 32
LLAMA_VOCAB_PRE_TYPE_LLAMA4 = 33
LLAMA_VOCAB_PRE_TYPE_PIXTRAL = 34
LLAMA_VOCAB_PRE_TYPE_SEED_CODER = 35











LLAMA_ROPE_TYPE_NONE = -1
LLAMA_ROPE_TYPE_NORM = 0
LLAMA_ROPE_TYPE_NEOX = GGML_ROPE_TYPE_NEOX = 2
LLAMA_ROPE_TYPE_MROPE = GGML_ROPE_TYPE_MROPE = 8
LLAMA_ROPE_TYPE_VISION = GGML_ROPE_TYPE_VISION = 24











LLAMA_TOKEN_TYPE_UNDEFINED = 0
LLAMA_TOKEN_TYPE_NORMAL = 1
LLAMA_TOKEN_TYPE_UNKNOWN = 2
LLAMA_TOKEN_TYPE_CONTROL = 3
LLAMA_TOKEN_TYPE_USER_DEFINED = 4
LLAMA_TOKEN_TYPE_UNUSED = 5
LLAMA_TOKEN_TYPE_BYTE = 6















LLAMA_TOKEN_ATTR_UNDEFINED = 0
LLAMA_TOKEN_ATTR_UNKNOWN = 1 << 0
LLAMA_TOKEN_ATTR_UNUSED = 1 << 1
LLAMA_TOKEN_ATTR_NORMAL = 1 << 2
LLAMA_TOKEN_ATTR_CONTROL = 1 << 3
LLAMA_TOKEN_ATTR_USER_DEFINED = 1 << 4
LLAMA_TOKEN_ATTR_BYTE = 1 << 5
LLAMA_TOKEN_ATTR_NORMALIZED = 1 << 6
LLAMA_TOKEN_ATTR_LSTRIP = 1 << 7
LLAMA_TOKEN_ATTR_RSTRIP = 1 << 8
LLAMA_TOKEN_ATTR_SINGLE_WORD = 1 << 9














































LLAMA_FTYPE_ALL_F32 = 0
LLAMA_FTYPE_MOSTLY_F16 = 1
LLAMA_FTYPE_MOSTLY_Q4_0 = 2
LLAMA_FTYPE_MOSTLY_Q4_1 = 3
LLAMA_FTYPE_MOSTLY_Q8_0 = 7
LLAMA_FTYPE_MOSTLY_Q5_0 = 8
LLAMA_FTYPE_MOSTLY_Q5_1 = 9
LLAMA_FTYPE_MOSTLY_Q2_K = 10
LLAMA_FTYPE_MOSTLY_Q3_K_S = 11
LLAMA_FTYPE_MOSTLY_Q3_K_M = 12
LLAMA_FTYPE_MOSTLY_Q3_K_L = 13
LLAMA_FTYPE_MOSTLY_Q4_K_S = 14
LLAMA_FTYPE_MOSTLY_Q4_K_M = 15
LLAMA_FTYPE_MOSTLY_Q5_K_S = 16
LLAMA_FTYPE_MOSTLY_Q5_K_M = 17
LLAMA_FTYPE_MOSTLY_Q6_K = 18
LLAMA_FTYPE_MOSTLY_IQ2_XXS = 19
LLAMA_FTYPE_MOSTLY_IQ2_XS = 20
LLAMA_FTYPE_MOSTLY_Q2_K_S = 21
LLAMA_FTYPE_MOSTLY_IQ3_XS = 22
LLAMA_FTYPE_MOSTLY_IQ3_XXS = 23
LLAMA_FTYPE_MOSTLY_IQ1_S = 24
LLAMA_FTYPE_MOSTLY_IQ4_NL = 25
LLAMA_FTYPE_MOSTLY_IQ3_S = 26
LLAMA_FTYPE_MOSTLY_IQ3_M = 27
LLAMA_FTYPE_MOSTLY_IQ2_S = 28
LLAMA_FTYPE_MOSTLY_IQ2_M = 29
LLAMA_FTYPE_MOSTLY_IQ4_XS = 30
LLAMA_FTYPE_MOSTLY_IQ1_M = 31
LLAMA_FTYPE_MOSTLY_BF16 = 32



LLAMA_FTYPE_MOSTLY_TQ1_0 = 36
LLAMA_FTYPE_MOSTLY_TQ2_0 = 37
LLAMA_FTYPE_MOSTLY_MXFP4_MOE = 38
LLAMA_FTYPE_GUESSED = 1024









LLAMA_ROPE_SCALING_TYPE_UNSPECIFIED = -1
LLAMA_ROPE_SCALING_TYPE_NONE = 0
LLAMA_ROPE_SCALING_TYPE_LINEAR = 1
LLAMA_ROPE_SCALING_TYPE_YARN = 2
LLAMA_ROPE_SCALING_TYPE_LONGROPE = 3
LLAMA_ROPE_SCALING_TYPE_MAX_VALUE = LLAMA_ROPE_SCALING_TYPE_LONGROPE









LLAMA_POOLING_TYPE_UNSPECIFIED = -1
LLAMA_POOLING_TYPE_NONE = 0
LLAMA_POOLING_TYPE_MEAN = 1
LLAMA_POOLING_TYPE_CLS = 2
LLAMA_POOLING_TYPE_LAST = 3
LLAMA_POOLING_TYPE_RANK = 4

LLAMA_FLASH_ATTN_TYPE_AUTO = -1
LLAMA_FLASH_ATTN_TYPE_DISABLED = 0
LLAMA_FLASH_ATTN_TYPE_ENABLED = 1






LLAMA_ATTENTION_TYPE_UNSPECIFIED = -1
LLAMA_ATTENTION_TYPE_CAUSAL = 0
LLAMA_ATTENTION_TYPE_NON_CAUSAL = 1







LLAMA_SPLIT_MODE_NONE = 0
LLAMA_SPLIT_MODE_LAYER = 1
LLAMA_SPLIT_MODE_ROW = 2







class llama_token_data(ctypes.Structure):
    """Used to store token data

    Attributes:
        id (llama_token): token id
        logit (float): log-odds of the token
        p (float): probability of the token"""

    if TYPE_CHECKING:
        id: llama_token
        logit: float
        p: float

    _fields_ = [
        ("id", llama_token),
        ("logit", ctypes.c_float),
        ("p", ctypes.c_float),
    ]


llama_token_data_p = ctypes.POINTER(llama_token_data)










class llama_token_data_array(ctypes.Structure):
    """Used to sample tokens given logits

    Attributes:
        data (ctypes.Array[llama_token_data]): token data
        size (int): size of the array
        selected (int): index in the data array (i.e. not the token id)
        sorted (bool): whether the array is sorted"""

    if TYPE_CHECKING:
        data: CtypesArray[llama_token_data]
        size: int
        selected: int
        sorted: bool

    _fields_ = [
        ("data", llama_token_data_p),
        ("size", ctypes.c_size_t),
        ("selected", ctypes.c_int64),
        ("sorted", ctypes.c_bool),
    ]


llama_token_data_array_p = ctypes.POINTER(llama_token_data_array)


llama_progress_callback = ctypes.CFUNCTYPE(
    ctypes.c_bool, ctypes.c_float, ctypes.c_void_p
)




























class llama_batch(ctypes.Structure):
    """Input data for llama_encode/llama_decode

    A llama_batch object can contain input about one or many sequences

    The provided arrays (i.e. token, embd, pos, etc.) must have size of n_tokens

    Attributes:
        n_tokens (int): number of tokens
        token (ctypes.Array[llama_token]): the token ids of the input (used when embd is NULL)
        embd (ctypes.Array[ctypes.ctypes.c_float]): token embeddings (i.e. float vector of size n_embd) (used when token is NULL)
        pos (ctypes.Array[ctypes.Array[llama_pos]]): the positions of the respective token in the sequence
        seq_id (ctypes.Array[ctypes.Array[llama_seq_id]]): the sequence to which the respective token belongs
        logits (ctypes.Array[ctypes.ctypes.c_int8]): if zero, the logits for the respective token will not be output
    """

    if TYPE_CHECKING:
        n_tokens: int
        token: CtypesArray[llama_token]
        embd: CtypesArray[ctypes.c_float]
        pos: CtypesArray[CtypesArray[llama_pos]]
        n_seq_id: CtypesArray[ctypes.c_int]
        seq_id: CtypesArray[CtypesArray[llama_seq_id]]
        logits: CtypesArray[ctypes.c_int8]

    _fields_ = [
        ("n_tokens", ctypes.c_int32),
        ("token", ctypes.POINTER(llama_token)),
        ("embd", ctypes.POINTER(ctypes.c_float)),
        ("pos", ctypes.POINTER(llama_pos)),
        ("n_seq_id", ctypes.POINTER(ctypes.c_int32)),
        ("seq_id", ctypes.POINTER(ctypes.POINTER(llama_seq_id))),
        ("logits", ctypes.POINTER(ctypes.c_int8)),
    ]








LLAMA_KV_OVERRIDE_TYPE_INT = 0
LLAMA_KV_OVERRIDE_TYPE_FLOAT = 1
LLAMA_KV_OVERRIDE_TYPE_BOOL = 2
LLAMA_KV_OVERRIDE_TYPE_STR = 3















class llama_model_kv_override_value(ctypes.Union):
    _fields_ = [
        ("val_i64", ctypes.c_int64),
        ("val_f64", ctypes.c_double),
        ("val_bool", ctypes.c_bool),
        ("val_str", ctypes.c_char * 128),
    ]

    if TYPE_CHECKING:
        val_i64: int
        val_f64: float
        val_bool: bool
        val_str: bytes


class llama_model_kv_override(ctypes.Structure):
    _fields_ = [
        ("tag", ctypes.c_int),
        ("key", ctypes.c_char * 128),
        ("value", llama_model_kv_override_value),
    ]

    if TYPE_CHECKING:
        tag: int
        key: bytes
        value: Union[int, float, bool, bytes]










































class llama_model_params(ctypes.Structure):
    """Parameters for llama_model

    Attributes:
        devices (ctypes.Array[ggml_backend_dev_t]): NULL-terminated list of devices to use for offloading (if NULL, all available devices are used)
        tensor_buft_overrides (ctypes.Array[llama_model_tensor_buft_override]): NULL-terminated list of buffer types to use for tensors that match a pattern
        n_gpu_layers (int): number of layers to store in VRAM
        split_mode (int): how to split the model across multiple GPUs
        main_gpu (int): the GPU that is used for the entire model when split_mode is LLAMA_SPLIT_MODE_NONE
        tensor_split (ctypes.Array[ctypes.ctypes.c_float]): proportion of the model (layers or rows) to offload to each GPU, size: llama_max_devices()
        progress_callback (llama_progress_callback): called with a progress value between 0.0 and 1.0. Pass NULL to disable. If the provided progress_callback returns true, model loading continues. If it returns false, model loading is immediately aborted.
        progress_callback_user_data (ctypes.ctypes.c_void_p): context pointer passed to the progress callback
        kv_overrides (ctypes.Array[llama_model_kv_override]): override key-value pairs of the model meta data
        vocab_only (bool): only load the vocabulary, no weights
        use_mmap (bool): use mmap if possible
        use_mlock (bool): force system to keep model in RAM
        check_tensors (bool): validate model tensor data
        use_extra_bufts (bool): use extra buffer types (used for weight repacking)"""

    if TYPE_CHECKING:
        devices: CtypesArray[ctypes.c_void_p]
        tensor_buft_overrides: CtypesArray[llama_model_tensor_buft_override]
        n_gpu_layers: int
        split_mode: int
        main_gpu: int
        tensor_split: CtypesArray[ctypes.c_float]
        progress_callback: Callable[[float, ctypes.c_void_p], bool]
        progress_callback_user_data: ctypes.c_void_p
        kv_overrides: CtypesArray[llama_model_kv_override]
        vocab_only: bool
        use_mmap: bool
        use_mlock: bool
        check_tensors: bool
        use_extra_bufts: bool

    _fields_ = [
        ("devices", ctypes.c_void_p),
        ("tensor_buft_overrides", ctypes.c_void_p),
        ("n_gpu_layers", ctypes.c_int32),
        ("split_mode", ctypes.c_int),
        ("main_gpu", ctypes.c_int32),
        ("tensor_split", ctypes.POINTER(ctypes.c_float)),
        ("progress_callback", llama_progress_callback),
        ("progress_callback_user_data", ctypes.c_void_p),
        ("kv_overrides", ctypes.POINTER(llama_model_kv_override)),
        ("vocab_only", ctypes.c_bool),
        ("use_mmap", ctypes.c_bool),
        ("use_mlock", ctypes.c_bool),
        ("check_tensors", ctypes.c_bool),
        ("use_extra_bufts", ctypes.c_bool),
    ]



















































class llama_context_params(ctypes.Structure):
    """Parameters for llama_context

    Attributes:
        n_ctx (int): text context, 0 = from model
        n_batch (int): logical maximum batch size that can be submitted to llama_decode
        n_ubatch (int): physical maximum batch size
        n_seq_max (int): max number of sequences (i.e. distinct states for recurrent models)
        n_threads (int): number of threads to use for generation
        n_threads_batch (int): number of threads to use for batch processing
        rope_scaling_type (int): RoPE scaling type, from `enum llama_rope_scaling_type`
        pooling_type (int): whether to pool (sum) embedding results by sequence id (ignored if no pooling layer)
        attention_type (int): attention type to use for embeddings
        rope_freq_base (float): RoPE base frequency, 0 = from model
        rope_freq_scale (float): RoPE frequency scaling factor, 0 = from model
        yarn_ext_factor (float): YaRN extrapolation mix factor, negative = from model
        yarn_attn_factor (float): YaRN magnitude scaling factor
        yarn_beta_fast (float): YaRN low correction dim
        yarn_beta_slow (float): YaRN high correction dim
        yarn_orig_ctx (int): YaRN original context size
        defrag_thold (float): defragment the KV cache if holes/size > thold, <= 0 disabled (default)
        cb_eval (ggml_backend_sched_eval_callback): callback for scheduling eval
        cb_eval_user_data (ctypes.ctypes.c_void_p): user data for cb_eval
        type_k (int): data type for K cache
        type_v (int): data type for V cache
        abort_callback (ggml_abort_callback): abort callback if it returns true, execution of llama_decode() will be aborted
        abort_callback_data (ctypes.ctypes.c_void_p): data for abort_callback
        embeddings (bool): if true, extract embeddings (together with logits)
        offload_kqv (bool): whether to offload the KQV ops (including the KV cache) to GPU
        flash_attn_type (int): when to enable flash attention
        no_perf (bool): whether to measure performance timings
        op_offload (bool): offload host tensor operations to device
        swa_full (bool): use full-size SWA cache
        kv_unified (bool): use a unified buffer across the input sequences when computing the attention
        samplers (ctypes.ctypes.c_void_p): backend sampler chain configuration pointer
        n_samplers (int): number of backend sampler chains
    """

    if TYPE_CHECKING:
        n_ctx: int
        n_batch: int
        n_ubatch: int
        n_seq_max: int
        n_threads: int
        n_threads_batch: int
        rope_scaling_type: int
        pooling_type: int
        attention_type: int
        rope_freq_base: float
        rope_freq_scale: float
        yarn_ext_factor: float
        yarn_attn_factor: float
        yarn_beta_fast: float
        yarn_beta_slow: float
        yarn_orig_ctx: int
        defrag_thold: float
        cb_eval: Callable[[ctypes.c_void_p, bool], bool]
        cb_eval_user_data: ctypes.c_void_p
        type_k: int
        type_v: int
        abort_callback: Callable[[ctypes.c_void_p], bool]
        abort_callback_data: ctypes.c_void_p
        embeddings: bool
        offload_kqv: bool
        flash_attn_type: int
        no_perf: bool
        op_offload: bool
        swa_full: bool
        kv_unified: bool
        samplers: ctypes.c_void_p
        n_samplers: int

    _fields_ = [
        ("n_ctx", ctypes.c_uint32),
        ("n_batch", ctypes.c_uint32),
        ("n_ubatch", ctypes.c_uint32),
        ("n_seq_max", ctypes.c_uint32),
        ("n_threads", ctypes.c_int32),
        ("n_threads_batch", ctypes.c_int32),
        ("rope_scaling_type", ctypes.c_int),
        ("pooling_type", ctypes.c_int),
        ("attention_type", ctypes.c_int),
        ("flash_attn_type", ctypes.c_int),
        ("rope_freq_base", ctypes.c_float),
        ("rope_freq_scale", ctypes.c_float),
        ("yarn_ext_factor", ctypes.c_float),
        ("yarn_attn_factor", ctypes.c_float),
        ("yarn_beta_fast", ctypes.c_float),
        ("yarn_beta_slow", ctypes.c_float),
        ("yarn_orig_ctx", ctypes.c_uint32),
        ("defrag_thold", ctypes.c_float),
        ("cb_eval", ggml_backend_sched_eval_callback),
        ("cb_eval_user_data", ctypes.c_void_p),
        ("type_k", ctypes.c_int),
        ("type_v", ctypes.c_int),
        ("abort_callback", ggml_abort_callback),
        ("abort_callback_data", ctypes.c_void_p),
        ("embeddings", ctypes.c_bool),
        ("offload_kqv", ctypes.c_bool),
        ("no_perf", ctypes.c_bool),
        ("op_offload", ctypes.c_bool),
        ("swa_full", ctypes.c_bool),
        ("kv_unified", ctypes.c_bool),
        ("samplers", ctypes.c_void_p),
        ("n_samplers", ctypes.c_size_t),
    ]








llama_log_callback = ctypes.CFUNCTYPE(
    None, ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p
)
"""Signature for logging events
Note that text includes the new line character at the end for most events.
If your logging mechanism cannot handle that, check if the last character is '\n' and strip it
if it exists.
It might not exist for progress report where '.' is output repeatedly."""


















class llama_model_quantize_params(ctypes.Structure):
    """Parameters for llama_model_quantize

    Attributes:
        nthread (int): number of threads to use for quantizing, if <=0 will use std::thread::hardware_concurrency()
        ftype (int): quantize to this llama_ftype
        output_tensor_type (int): output tensor type
        token_embedding_type (int): token embeddings tensor type
        allow_requantize (bool): allow quantizing non-f32/f16 tensors
        quantize_output_tensor (bool): quantize output.weight
        only_copy (bool): only copy tensors - ftype, allow_requantize and quantize_output_tensor are ignored
        pure (bool): quantize all tensors to the default type
        keep_split (bool): quantize to the same number of shards
        imatrix (ctypes.c_void_p): pointer to importance matrix data
        kv_overrides (ctypes.c_void_p): pointer to vector containing overrides
        tensor_types (ctypes.c_void_p): pointer to vector containing tensor types
        prune_layers (ctypes.c_void_p): pointer to vector containing layer indices to prune
    """

    if TYPE_CHECKING:
        nthread: int
        ftype: int
        output_tensor_type: int
        token_embedding_type: int
        allow_requantize: bool
        quantize_output_tensor: bool
        only_copy: bool
        pure: bool
        keep_split: bool
        imatrix: ctypes.c_void_p
        kv_overrides: ctypes.c_void_p
        tensor_types: ctypes.c_void_p
        prune_layers: ctypes.c_void_p

    _fields_ = [
        ("nthread", ctypes.c_int32),
        ("ftype", ctypes.c_int),
        ("output_tensor_type", ctypes.c_int),
        ("token_embedding_type", ctypes.c_int),
        ("allow_requantize", ctypes.c_bool),
        ("quantize_output_tensor", ctypes.c_bool),
        ("only_copy", ctypes.c_bool),
        ("pure", ctypes.c_bool),
        ("keep_split", ctypes.c_bool),
        ("imatrix", ctypes.c_void_p),
        ("kv_overrides", ctypes.c_void_p),
        ("tensor_types", ctypes.c_void_p),
        ("prune_layers", ctypes.c_void_p),
    ]






class llama_logit_bias(ctypes.Structure):
    """Used to store logit bias

    Attributes:
        token (llama_token): token id
        bias (float): bias"""

    if TYPE_CHECKING:
        token: llama_token
        bias: float

    _fields_ = [
        ("token", llama_token),
        ("bias", ctypes.c_float),
    ]


llama_logit_bias_p = ctypes.POINTER(llama_logit_bias)





class llama_sampler_chain_params(ctypes.Structure):
    """Parameters for llama_sampler_chain

    Attributes:
        no_perf (bool): whether to measure performance timings"""

    if TYPE_CHECKING:
        no_perf: bool

    _fields_ = [
        ("no_perf", ctypes.c_bool),
    ]







class llama_chat_message(ctypes.Structure):
    _fields_ = [
        ("role", ctypes.c_char_p),
        ("content", ctypes.c_char_p),
    ]




llama_adapter_lora_p = ctypes.c_void_p
llama_adapter_lora_p_ctypes = ctypes.POINTER(ctypes.c_void_p)




@ctypes_function(
    "llama_model_default_params",
    [],
    llama_model_params,
)
def llama_model_default_params() -> llama_model_params:
    """Get default parameters for llama_model"""
    ...



@ctypes_function(
    "llama_context_default_params",
    [],
    llama_context_params,
)
def llama_context_default_params() -> llama_context_params:
    """Get default parameters for llama_context"""
    ...



@ctypes_function(
    "llama_sampler_chain_default_params",
    [],
    llama_sampler_chain_params,
)
def llama_sampler_chain_default_params() -> llama_sampler_chain_params:
    """Get default parameters for llama_sampler_chain"""
    ...



@ctypes_function(
    "llama_model_quantize_default_params",
    [],
    llama_model_quantize_params,
)
def llama_model_quantize_default_params() -> llama_model_quantize_params:
    """Get default parameters for llama_model_quantize"""
    ...






@ctypes_function(
    "llama_backend_init",
    [],
    None,
)
def llama_backend_init():
    """Initialize the llama + ggml backend
    Call once at the start of the program"""
    ...











GGML_NUMA_STRATEGY_DISABLED = 0
GGML_NUMA_STRATEGY_DISTRIBUTE = 1
GGML_NUMA_STRATEGY_ISOLATE = 2
GGML_NUMA_STRATEGY_NUMACTL = 3
GGML_NUMA_STRATEGY_MIRROR = 4
GGML_NUMA_STRATEGY_COUNT = 5




@ctypes_function(
    "llama_backend_free",
    [],
    None,
)
def llama_backend_free():
    """Call once at the end of the program - currently only used for MPI"""
    ...




@ctypes_function(
    "llama_numa_init",
    [ctypes.c_int],
    None,
)
def llama_numa_init(numa: int, /):
    ...


















@ctypes_function(
    "llama_load_model_from_file",
    [ctypes.c_char_p, llama_model_params],
    llama_model_p_ctypes,
)
def llama_load_model_from_file(
    path_model: bytes, params: llama_model_params, /
) -> Optional[llama_model_p]:
    ...








@ctypes_function(
    "llama_model_load_from_file",
    [ctypes.c_char_p, llama_model_params],
    llama_model_p_ctypes,
)
def llama_model_load_from_file(
    path_model: bytes, params: llama_model_params, /
) -> Optional[llama_model_p]:
    """Load the model from a file

    If the file is split into multiple parts, the file name must follow this pattern: <name>-%05d-of-%05d.gguf

    If the split file name does not follow this pattern, use llama_model_load_from_splits"""
    ...








@ctypes_function(
    "llama_model_load_from_splits",
    [ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t, llama_model_params],
    llama_model_p_ctypes,
)
def llama_model_load_from_splits(
    paths: List[bytes], n_paths: int, params: llama_model_params, /
) -> Optional[llama_model_p]:
    """Load the model from multiple splits (support custom naming scheme)

    The paths must be in the correct order"""
    ...





@ctypes_function(
    "llama_model_save_to_file",
    [llama_model_p_ctypes, ctypes.c_char_p],
    None,
)
def llama_model_save_to_file(model: llama_model_p, path_model: bytes, /):
    """Save the model to a file"""
    ...




@ctypes_function(
    "llama_free_model",
    [llama_model_p_ctypes],
    None,
)
def llama_free_model(model: llama_model_p, /):
    ...



@ctypes_function(
    "llama_model_free",
    [llama_model_p_ctypes],
    None,
)
def llama_model_free(model: llama_model_p, /):
    ...





@ctypes_function(
    "llama_init_from_model",
    [llama_model_p_ctypes, llama_context_params],
    llama_context_p_ctypes,
)
def llama_init_from_model(
    model: llama_model_p, params: llama_context_params, /
) -> Optional[llama_context_p]:
    ...






@ctypes_function(
    "llama_init_from_model",
    [llama_model_p_ctypes, llama_context_params],
    llama_context_p_ctypes,
)
def llama_init_from_model(
    model: llama_model_p, params: llama_context_params, /
) -> Optional[llama_context_p]:
    ...


# DEPRECATED(LLAMA_API struct llama_context * llama_new_context_with_model(
#                  struct llama_model * model,
#         struct llama_context_params   params),
#         "use llama_init_from_model instead");
@ctypes_function(
    "llama_new_context_with_model",
    [llama_model_p_ctypes, llama_context_params],
    llama_context_p_ctypes,
)
def llama_new_context_with_model(
    model: llama_model_p, params: llama_context_params, /
) -> Optional[llama_context_p]:
    ...




@ctypes_function(
    "llama_free",
    [llama_context_p_ctypes],
    None,
)
def llama_free(ctx: llama_context_p, /):
    """Frees all allocated memory"""
    ...



@ctypes_function(
    "llama_time_us",
    [],
    ctypes.c_int64,
)
def llama_time_us() -> int:
    ...



@ctypes_function("llama_max_devices", [], ctypes.c_size_t)
def llama_max_devices() -> int:
    ...



@ctypes_function("llama_max_parallel_sequences", [], ctypes.c_size_t)
def llama_max_parallel_sequences() -> int:
    ...



@ctypes_function("llama_supports_mmap", [], ctypes.c_bool)
def llama_supports_mmap() -> bool:
    ...



@ctypes_function("llama_supports_mlock", [], ctypes.c_bool)
def llama_supports_mlock() -> bool:
    ...



@ctypes_function("llama_supports_gpu_offload", [], ctypes.c_bool)
def llama_supports_gpu_offload() -> bool:
    ...



@ctypes_function("llama_supports_rpc", [], ctypes.c_bool)
def llama_supports_rpc() -> bool:
    ...



@ctypes_function("llama_n_ctx", [llama_context_p_ctypes], ctypes.c_uint32)
def llama_n_ctx(ctx: llama_context_p, /) -> int:
    ...



@ctypes_function("llama_n_batch", [llama_context_p_ctypes], ctypes.c_uint32)
def llama_n_batch(ctx: llama_context_p, /) -> int:
    ...



@ctypes_function("llama_n_ubatch", [llama_context_p_ctypes], ctypes.c_uint32)
def llama_n_ubatch(ctx: llama_context_p, /) -> int:
    ...



@ctypes_function("llama_n_seq_max", [llama_context_p_ctypes], ctypes.c_uint32)
def llama_n_seq_max(ctx: llama_context_p, /) -> int:
    ...



@ctypes_function("llama_n_ctx_train", [llama_model_p_ctypes], ctypes.c_int32)
def llama_n_ctx_train(model: llama_model_p, /) -> int:
    ...



@ctypes_function("llama_n_embd", [llama_model_p_ctypes], ctypes.c_int32)
def llama_n_embd(model: llama_model_p, /) -> int:
    ...



@ctypes_function("llama_n_layer", [llama_model_p_ctypes], ctypes.c_int32)
def llama_n_layer(model: llama_model_p, /) -> int:
    ...



@ctypes_function("llama_n_head", [llama_model_p_ctypes], ctypes.c_int32)
def llama_n_head(model: llama_model_p, /) -> int:
    ...



@ctypes_function("llama_n_vocab", [llama_vocab_p_ctypes], ctypes.c_int32)
def llama_n_vocab(model: llama_vocab_p, /) -> int:
    ...



@ctypes_function("llama_get_model", [llama_context_p_ctypes], llama_model_p_ctypes)
def llama_get_model(ctx: llama_context_p, /) -> Optional[llama_model_p]:
    ...



@ctypes_function("llama_get_memory", [llama_context_p_ctypes], llama_memory_t_ctypes)
def llama_get_memory(ctx: llama_context_p, /) -> Optional[llama_memory_t]:
    """Get the memory for the context"""
    ...



@ctypes_function("llama_pooling_type", [llama_context_p_ctypes], ctypes.c_int)
def llama_pooling_type(ctx: llama_context_p, /) -> int:
    ...



@ctypes_function(
    "llama_get_kv_self",
    [llama_context_p_ctypes],
    llama_kv_cache_p_ctypes,
)
def llama_get_kv_self(ctx: llama_context_p, /) -> Optional[llama_kv_cache_p]:
    """Get the KV cache for self-attention (DEPRECATED)"""
    ...



@ctypes_function("llama_model_get_vocab", [llama_model_p_ctypes], llama_vocab_p_ctypes)
def llama_model_get_vocab(model: llama_model_p, /) -> Optional[llama_vocab_p]:
    ...



@ctypes_function("llama_model_rope_type", [llama_model_p_ctypes], ctypes.c_int)
def llama_model_rope_type(model: llama_model_p, /) -> int:
    ...



@ctypes_function("llama_model_n_ctx_train", [llama_model_p_ctypes], ctypes.c_int32)
def llama_model_n_ctx_train(model: llama_model_p, /) -> int:
    ...



@ctypes_function("llama_model_n_embd", [llama_model_p_ctypes], ctypes.c_int32)
def llama_model_n_embd(model: llama_model_p, /) -> int:
    ...



@ctypes_function("llama_model_n_layer", [llama_model_p_ctypes], ctypes.c_int32)
def llama_model_n_layer(model: llama_model_p, /) -> int:
    ...



@ctypes_function("llama_model_n_head", [llama_model_p_ctypes], ctypes.c_int32)
def llama_model_n_head(model: llama_model_p, /) -> int:
    ...



@ctypes_function("llama_model_n_head_kv", [llama_model_p_ctypes], ctypes.c_int32)
def llama_model_n_head_kv(model: llama_model_p, /) -> int:
    ...



@ctypes_function("llama_model_n_swa", [llama_model_p_ctypes], ctypes.c_int32)
def llama_model_n_swa(model: llama_model_p, /) -> int:
    ...




@ctypes_function("llama_model_rope_freq_scale_train", [llama_model_p_ctypes], ctypes.c_float)
def llama_model_rope_freq_scale_train(model: llama_model_p, /) -> float:
    ...





@ctypes_function("llama_model_n_cls_out", [llama_model_p_ctypes], ctypes.c_uint32)
def llama_model_n_cls_out(model: llama_model_p, /) -> int:
    """Returns the number of classifier outputs (only valid for classifier models)"""
    ...




@ctypes_function("llama_model_cls_label", [llama_model_p_ctypes, ctypes.c_uint32], ctypes.c_char_p)
def llama_model_cls_label(model: llama_model_p, i: int, /) -> Optional[bytes]:
    """Returns label of classifier output by index. Returns None if no label provided"""
    ...



@ctypes_function("llama_vocab_type", [llama_vocab_p_ctypes], ctypes.c_int)
def llama_vocab_type(vocab: llama_vocab_p, /) -> int:
    ...



@ctypes_function("llama_vocab_n_tokens", [llama_vocab_p_ctypes], ctypes.c_int32)
def llama_vocab_n_tokens(vocab: llama_vocab_p, /) -> int:
    ...











@ctypes_function(
    "llama_model_meta_val_str",
    [
        llama_model_p_ctypes,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_size_t,
    ],
    ctypes.c_int32,
)
def llama_model_meta_val_str(
    model: llama_model_p,
    key: Union[ctypes.c_char_p, bytes],
    buf: bytes,
    buf_size: int,
    /,
) -> int:
    """Get metadata value as a string by key name"""
    ...




@ctypes_function("llama_model_meta_count", [llama_model_p_ctypes], ctypes.c_int32)
def llama_model_meta_count(model: llama_model_p, /) -> int:
    """Get the number of metadata key/value pairs"""
    ...




@ctypes_function(
    "llama_model_meta_key_by_index",
    [
        llama_model_p_ctypes,
        ctypes.c_int32,
        ctypes.c_char_p,
        ctypes.c_size_t,
    ],
    ctypes.c_int32,
)
def llama_model_meta_key_by_index(
    model: llama_model_p,
    i: Union[ctypes.c_int, int],
    buf: Union[bytes, CtypesArray[ctypes.c_char]],
    buf_size: int,
    /,
) -> int:
    """Get metadata key name by index"""
    ...




@ctypes_function(
    "llama_model_meta_val_str_by_index",
    [
        llama_model_p_ctypes,
        ctypes.c_int32,
        ctypes.c_char_p,
        ctypes.c_size_t,
    ],
    ctypes.c_int32,
)
def llama_model_meta_val_str_by_index(
    model: llama_model_p,
    i: Union[ctypes.c_int, int],
    buf: Union[bytes, CtypesArray[ctypes.c_char]],
    buf_size: int,
    /,
) -> int:
    """Get metadata value as a string by index"""
    ...




@ctypes_function(
    "llama_model_desc",
    [llama_model_p_ctypes, ctypes.c_char_p, ctypes.c_size_t],
    ctypes.c_int32,
)
def llama_model_desc(
    model: llama_model_p,
    buf: Union[bytes, CtypesArray[ctypes.c_char]],
    buf_size: Union[ctypes.c_size_t, int],
    /,
) -> int:
    """Get a string describing the model type"""
    ...




@ctypes_function("llama_model_size", [llama_model_p_ctypes], ctypes.c_uint64)
def llama_model_size(model: llama_model_p, /) -> int:
    """Returns the total size of all the tensors in the model in bytes"""
    ...





@ctypes_function("llama_model_chat_template", [llama_model_p_ctypes, ctypes.c_char_p], ctypes.c_char_p)
def llama_model_chat_template(model: llama_model_p, name: Optional[bytes], /) -> Optional[bytes]:
    """Get the default chat template. Returns None if not available
    If name is None, returns the default chat template"""
    ...




@ctypes_function("llama_model_n_params", [llama_model_p_ctypes], ctypes.c_uint64)
def llama_model_n_params(model: llama_model_p, /) -> int:
    """Returns the total number of parameters in the model"""
    ...




@ctypes_function("llama_model_has_encoder", [llama_model_p_ctypes], ctypes.c_bool)
def llama_model_has_encoder(model: llama_model_p, /) -> bool:
    """Returns true if the model contains an encoder that requires llama_encode() call"""
    ...




@ctypes_function("llama_model_has_decoder", [llama_model_p_ctypes], ctypes.c_bool)
def llama_model_has_decoder(model: llama_model_p, /) -> bool:
    """Returns true if the model contains a decoder that requires llama_decode() call"""
    ...





@ctypes_function(
    "llama_model_decoder_start_token", [llama_model_p_ctypes], ctypes.c_int32
)
def llama_model_decoder_start_token(model: llama_model_p, /) -> int:
    """For encoder-decoder models, this function returns id of the token that must be provided
    to the decoder to start generating output sequence. For other models, it returns -1.
    """
    ...




@ctypes_function("llama_model_is_recurrent", [llama_model_p_ctypes], ctypes.c_bool)
def llama_model_is_recurrent(model: llama_model_p, /) -> bool:
    """Returns true if the model is recurrent (like Mamba, RWKV, etc.)"""
    ...




@ctypes_function("llama_model_is_diffusion", [llama_model_p_ctypes], ctypes.c_bool)
def llama_model_is_diffusion(model: llama_model_p, /) -> bool:
    """Returns true if the model is diffusion-based (like LLaDA, Dream, etc.)"""
    ...







@ctypes_function(
    "llama_model_quantize",
    [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.POINTER(llama_model_quantize_params),
    ],
    ctypes.c_uint32,
)
def llama_model_quantize(
    fname_inp: bytes,
    fname_out: bytes,
    params: CtypesPointerOrRef[llama_model_quantize_params],
    /,
) -> int:
    """Returns 0 on success"""
    ...










@ctypes_function(
    "llama_adapter_lora_init",
    [llama_model_p_ctypes, ctypes.c_char_p],
    llama_adapter_lora_p_ctypes,
)
def llama_adapter_lora_init(
    model: llama_model_p, path_lora: bytes, /
) -> Optional[llama_adapter_lora_p]:
    ...





@ctypes_function(
    "llama_adapter_lora_free",
    [llama_adapter_lora_p_ctypes],
    None,
)
def llama_adapter_lora_free(adapter: llama_adapter_lora_p, /):
    ...











@ctypes_function(
    "llama_set_adapter_lora",
    [llama_context_p_ctypes, llama_adapter_lora_p_ctypes, ctypes.c_float],
    ctypes.c_int32,
)
def llama_set_adapter_lora(
    ctx: llama_context_p, adapter: llama_adapter_lora_p, scale: float, /
) -> int:
    """Add a loaded LoRA adapter to given context
    This will not modify model's weight"""
    ...







@ctypes_function(
    "llama_rm_adapter_lora",
    [llama_context_p_ctypes, llama_adapter_lora_p_ctypes],
    ctypes.c_int32,
)
def llama_rm_adapter_lora(
    ctx: llama_context_p, adapter: llama_adapter_lora_p, /
) -> int:
    """Remove a specific LoRA adapter from given context
    Return -1 if the adapter is not present in the context"""
    ...




@ctypes_function(
    "llama_clear_adapter_lora",
    [llama_context_p_ctypes],
    None,
)
def llama_clear_adapter_lora(ctx: llama_context_p, /):
    """Remove all LoRA adapters from given context"""
    ...















@ctypes_function(
    "llama_apply_adapter_cvec",
    [
        llama_context_p_ctypes,
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_size_t,
        ctypes.c_int32,
        ctypes.c_int32,
        ctypes.c_int32,
    ],
    ctypes.c_int32,
)
def llama_apply_adapter_cvec(
    ctx: llama_context_p,
    data: CtypesPointerOrRef[ctypes.c_float],
    len: int,
    n_embd: int,
    il_start: int,
    il_end: int,
    /,
) -> int:
    """Apply a loaded control vector to a llama_context, or if data is NULL, clear
    the currently loaded vector.
    n_embd should be the size of a single layer's control, and data should point
    to an n_embd x n_layers buffer starting from layer 1.
    il_start and il_end are the layer range the vector should apply to (both inclusive)
    See llama_control_vector_load in common to load a control vector."""
    ...











@ctypes_function(
    "llama_memory_clear",
    [llama_memory_t_ctypes, ctypes.c_bool],
    None,
)
def llama_memory_clear(mem: llama_memory_t, data: bool, /):
    """Clear the memory contents
    If data == true, the data buffers will also be cleared together with the metadata"""
    ...












@ctypes_function(
    "llama_memory_seq_rm",
    [
        llama_memory_t_ctypes,
        llama_seq_id,
        llama_pos,
        llama_pos,
    ],
    ctypes.c_bool,
)
def llama_memory_seq_rm(
    mem: llama_memory_t,
    seq_id: Union[llama_seq_id, int],
    p0: Union[llama_pos, int],
    p1: Union[llama_pos, int],
    /,
) -> bool:
    """Removes all tokens that belong to the specified sequence and have positions in [p0, p1)

    Returns false if a partial sequence cannot be removed. Removing a whole sequence never fails

    seq_id < 0 : match any sequence
    p0 < 0     : [0,  p1]
    p1 < 0     : [p0, inf)"""
    ...











@ctypes_function(
    "llama_memory_seq_cp",
    [
        llama_memory_t_ctypes,
        llama_seq_id,
        llama_seq_id,
        llama_pos,
        llama_pos,
    ],
    None,
)
def llama_memory_seq_cp(
    mem: llama_memory_t,
    seq_id_src: Union[llama_seq_id, int],
    seq_id_dst: Union[llama_seq_id, int],
    p0: Union[llama_pos, int],
    p1: Union[llama_pos, int],
    /,
):
    """Copy all tokens that belong to the specified sequence to another sequence
    p0 < 0 : [0,  p1]
    p1 < 0 : [p0, inf)"""
    ...






@ctypes_function(
    "llama_memory_seq_keep", [llama_memory_t_ctypes, llama_seq_id], None
)
def llama_memory_seq_keep(mem: llama_memory_t, seq_id: Union[llama_seq_id, int], /):
    """Removes all tokens that do not belong to the specified sequence"""
    ...











@ctypes_function(
    "llama_memory_seq_add",
    [
        llama_memory_t_ctypes,
        llama_seq_id,
        llama_pos,
        llama_pos,
        llama_pos,
    ],
    None,
)
def llama_memory_seq_add(
    mem: llama_memory_t,
    seq_id: Union[llama_seq_id, int],
    p0: Union[llama_pos, int],
    p1: Union[llama_pos, int],
    delta: Union[llama_pos, int],
    /,
):
    """Adds relative position "delta" to all tokens that belong to the specified sequence and have positions in [p0, p1)
    p0 < 0 : [0,  p1]
    p1 < 0 : [p0, inf)"""
    ...











@ctypes_function(
    "llama_memory_seq_div",
    [
        llama_memory_t_ctypes,
        llama_seq_id,
        llama_pos,
        llama_pos,
        ctypes.c_int,
    ],
    None,
)
def llama_memory_seq_div(
    mem: llama_memory_t,
    seq_id: Union[llama_seq_id, int],
    p0: Union[llama_pos, int],
    p1: Union[llama_pos, int],
    d: Union[ctypes.c_int, int],
    /,
):
    """Integer division of the positions by factor of `d > 1`
    p0 < 0 : [0,  p1]
    p1 < 0 : [p0, inf)"""
    ...









@ctypes_function(
    "llama_memory_seq_pos_min", [llama_memory_t_ctypes, llama_seq_id], llama_pos
)
def llama_memory_seq_pos_min(
    mem: llama_memory_t, seq_id: Union[llama_seq_id, int], /
) -> int:
    """Returns the smallest position present in the memory for the specified sequence
    This is typically non-zero only for SWA caches
    Return -1 if the sequence is empty"""
    ...








@ctypes_function(
    "llama_memory_seq_pos_max", [llama_memory_t_ctypes, llama_seq_id], llama_pos
)
def llama_memory_seq_pos_max(
    mem: llama_memory_t, seq_id: Union[llama_seq_id, int], /
) -> int:
    """Returns the largest position present in the memory for the specified sequence
    Return -1 if the sequence is empty"""
    ...




@ctypes_function("llama_memory_can_shift", [llama_memory_t_ctypes], ctypes.c_bool)
def llama_memory_can_shift(mem: llama_memory_t, /) -> bool:
    """Check if the memory supports shifting"""
    ...










@ctypes_function(
    "llama_kv_self_n_tokens", [llama_context_p_ctypes], ctypes.c_int32
)
def llama_kv_self_n_tokens(ctx: llama_context_p, /) -> int:
    """Returns the number of tokens in the KV cache (slow, use only for debug) (DEPRECATED)"""
    ...





@ctypes_function(
    "llama_kv_self_used_cells", [llama_context_p_ctypes], ctypes.c_int32
)
def llama_kv_self_used_cells(ctx: llama_context_p, /) -> int:
    """Returns the number of used KV cells (DEPRECATED)"""
    ...






@ctypes_function(
    "llama_kv_self_clear", [llama_context_p_ctypes], None
)
def llama_kv_self_clear(ctx: llama_context_p, /):
    """Clear the KV cache (DEPRECATED)"""
    ...













@ctypes_function(
    "llama_kv_self_seq_rm",
    [
        llama_context_p_ctypes,
        llama_seq_id,
        llama_pos,
        llama_pos,
    ],
    ctypes.c_bool,
)
def llama_kv_self_seq_rm(
    ctx: llama_context_p,
    seq_id: Union[llama_seq_id, int],
    p0: Union[llama_pos, int],
    p1: Union[llama_pos, int],
    /,
) -> bool:
    """Remove tokens from KV cache (DEPRECATED)"""
    ...













@ctypes_function(
    "llama_kv_self_seq_cp",
    [
        llama_context_p_ctypes,
        llama_seq_id,
        llama_seq_id,
        llama_pos,
        llama_pos,
    ],
    None,
)
def llama_kv_self_seq_cp(
    ctx: llama_context_p,
    seq_id_src: Union[llama_seq_id, int],
    seq_id_dst: Union[llama_seq_id, int],
    p0: Union[llama_pos, int],
    p1: Union[llama_pos, int],
    /,
):
    """Copy tokens in KV cache (DEPRECATED)"""
    ...







@ctypes_function(
    "llama_kv_self_seq_keep", [llama_context_p_ctypes, llama_seq_id], None
)
def llama_kv_self_seq_keep(ctx: llama_context_p, seq_id: Union[llama_seq_id, int], /):
    """Keep only specified sequence in KV cache (DEPRECATED)"""
    ...














@ctypes_function(
    "llama_kv_self_seq_add",
    [
        llama_context_p_ctypes,
        llama_seq_id,
        llama_pos,
        llama_pos,
        llama_pos,
    ],
    None,
)
def llama_kv_self_seq_add(
    ctx: llama_context_p,
    seq_id: Union[llama_seq_id, int],
    p0: Union[llama_pos, int],
    p1: Union[llama_pos, int],
    delta: Union[llama_pos, int],
    /,
):
    """Add delta to sequence positions in KV cache (DEPRECATED)"""
    ...














@ctypes_function(
    "llama_kv_self_seq_div",
    [
        llama_context_p_ctypes,
        llama_seq_id,
        llama_pos,
        llama_pos,
        ctypes.c_int,
    ],
    None,
)
def llama_kv_self_seq_div(
    ctx: llama_context_p,
    seq_id: Union[llama_seq_id, int],
    p0: Union[llama_pos, int],
    p1: Union[llama_pos, int],
    d: Union[ctypes.c_int, int],
    /,
):
    """Divide sequence positions in KV cache (DEPRECATED)"""
    ...










@ctypes_function(
    "llama_kv_self_seq_pos_min", [llama_context_p_ctypes, llama_seq_id], llama_pos
)
def llama_kv_self_seq_pos_min(
    ctx: llama_context_p, seq_id: Union[llama_seq_id, int], /
) -> int:
    """Returns the smallest position in KV cache for sequence (DEPRECATED)"""
    ...









@ctypes_function(
    "llama_kv_self_seq_pos_max", [llama_context_p_ctypes, llama_seq_id], llama_pos
)
def llama_kv_self_seq_pos_max(
    ctx: llama_context_p, seq_id: Union[llama_seq_id, int], /
) -> int:
    """Returns the largest position in KV cache for sequence (DEPRECATED)"""
    ...







@ctypes_function("llama_kv_self_defrag", [llama_context_p_ctypes], None)
def llama_kv_self_defrag(ctx: llama_context_p, /):
    """Defragment the KV cache (DEPRECATED)"""
    ...





@ctypes_function("llama_kv_self_can_shift", [llama_context_p_ctypes], ctypes.c_bool)
def llama_kv_self_can_shift(ctx: llama_context_p, /) -> bool:
    """Check if the context supports KV cache shifting (DEPRECATED)"""
    ...





@ctypes_function("llama_kv_self_update", [llama_context_p_ctypes], None)
def llama_kv_self_update(ctx: llama_context_p, /):
    """Apply the KV cache updates (DEPRECATED)"""
    ...










@ctypes_function("llama_state_get_size", [llama_context_p_ctypes], ctypes.c_size_t)
def llama_state_get_size(ctx: llama_context_p, /) -> int:
    """Returns the *actual* size in bytes of the state (logits, embedding and memory)"""
    ...




@ctypes_function("llama_get_state_size", [llama_context_p_ctypes], ctypes.c_size_t)
def llama_get_state_size(ctx: llama_context_p, /) -> int:
    """Returns the size in bytes of the state (DEPRECATED)"""
    ...









@ctypes_function(
    "llama_state_get_data",
    [
        llama_context_p_ctypes,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
    ],
    ctypes.c_size_t,
)
def llama_state_get_data(
    ctx: llama_context_p,
    dst: CtypesArray[ctypes.c_uint8],
    size: Union[ctypes.c_size_t, int],
    /,
) -> int:
    """Copies the state to the specified destination address.
    Destination needs to have allocated enough memory.
    Returns the number of bytes copied"""
    ...






@ctypes_function(
    "llama_copy_state_data",
    [
        llama_context_p_ctypes,
        ctypes.POINTER(ctypes.c_uint8),
    ],
    ctypes.c_size_t,
)
def llama_copy_state_data(
    ctx: llama_context_p, dst: CtypesArray[ctypes.c_uint8], /
) -> int:
    """Copies the state to the specified destination address (DEPRECATED)"""
    ...








@ctypes_function(
    "llama_state_set_data",
    [llama_context_p_ctypes, ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t],
    ctypes.c_size_t,
)
def llama_state_set_data(
    ctx: llama_context_p,
    src: CtypesArray[ctypes.c_uint8],
    size: Union[ctypes.c_size_t, int],
    /,
) -> int:
    """Set the state reading from the specified address
    Returns the number of bytes read"""
    ...






@ctypes_function(
    "llama_set_state_data",
    [llama_context_p_ctypes, ctypes.POINTER(ctypes.c_uint8)],
    ctypes.c_size_t,
)
def llama_set_state_data(
    ctx: llama_context_p, src: CtypesArray[ctypes.c_uint8], /
) -> int:
    """Set the state reading from the specified address (DEPRECATED)"""
    ...









@ctypes_function(
    "llama_state_load_file",
    [
        llama_context_p_ctypes,
        ctypes.c_char_p,
        llama_token_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ],
    ctypes.c_bool,
)
def llama_state_load_file(
    ctx: llama_context_p,
    path_session: bytes,
    tokens_out: CtypesArray[llama_token],
    n_token_capacity: Union[ctypes.c_size_t, int],
    n_token_count_out: CtypesPointerOrRef[ctypes.c_size_t],
    /,
) -> bool:
    ...









@ctypes_function(
    "llama_load_session_file",
    [
        llama_context_p_ctypes,
        ctypes.c_char_p,
        llama_token_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ],
    ctypes.c_bool,
)
def llama_load_session_file(
    ctx: llama_context_p,
    path_session: bytes,
    tokens_out: CtypesArray[llama_token],
    n_token_capacity: Union[ctypes.c_size_t, int],
    n_token_count_out: CtypesPointerOrRef[ctypes.c_size_t],
    /,
) -> bool:
    ...







@ctypes_function(
    "llama_state_save_file",
    [
        llama_context_p_ctypes,
        ctypes.c_char_p,
        llama_token_p,
        ctypes.c_size_t,
    ],
    ctypes.c_bool,
)
def llama_state_save_file(
    ctx: llama_context_p,
    path_session: bytes,
    tokens: CtypesArray[llama_token],
    n_token_count: Union[ctypes.c_size_t, int],
    /,
) -> bool:
    ...








@ctypes_function(
    "llama_save_session_file",
    [
        llama_context_p_ctypes,
        ctypes.c_char_p,
        llama_token_p,
        ctypes.c_size_t,
    ],
    ctypes.c_bool,
)
def llama_save_session_file(
    ctx: llama_context_p,
    path_session: bytes,
    tokens: CtypesArray[llama_token],
    n_token_count: Union[ctypes.c_size_t, int],
    /,
) -> bool:
    ...






@ctypes_function(
    "llama_state_seq_get_size",
    [llama_context_p_ctypes, llama_seq_id],
    ctypes.c_size_t,
)
def llama_state_seq_get_size(ctx: llama_context_p, seq_id: llama_seq_id, /) -> int:
    """Get the exact size needed to copy the state of a single sequence"""
    ...








@ctypes_function(
    "llama_state_seq_get_data",
    [
        llama_context_p_ctypes,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        llama_seq_id,
    ],
    ctypes.c_size_t,
)
def llama_state_seq_get_data(
    ctx: llama_context_p,
    dst: CtypesArray[ctypes.c_uint8],
    size: Union[ctypes.c_size_t, int],
    seq_id: llama_seq_id,
    /,
) -> int:
    """Copy the state of a single sequence into the specified buffer"""
    ...











@ctypes_function(
    "llama_state_seq_set_data",
    [
        llama_context_p_ctypes,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        llama_seq_id,
    ],
    ctypes.c_size_t,
)
def llama_state_seq_set_data(
    ctx: llama_context_p,
    src: CtypesArray[ctypes.c_uint8],
    size: Union[ctypes.c_size_t, int],
    dest_seq_id: llama_seq_id,
    /,
) -> int:
    """Copy the sequence data into the specified sequence"""
    ...








@ctypes_function(
    "llama_state_seq_save_file",
    [
        llama_context_p_ctypes,
        ctypes.c_char_p,
        llama_seq_id,
        llama_token_p,
        ctypes.c_size_t,
    ],
    ctypes.c_size_t,
)
def llama_state_seq_save_file(
    ctx: llama_context_p,
    filepath: bytes,
    seq_id: llama_seq_id,
    tokens: CtypesArray[llama_token],
    n_token_count: Union[ctypes.c_size_t, int],
    /,
) -> int:
    ...









@ctypes_function(
    "llama_state_seq_load_file",
    [
        llama_context_p_ctypes,
        ctypes.c_char_p,
        llama_seq_id,
        llama_token_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ],
    ctypes.c_size_t,
)
def llama_state_seq_load_file(
    ctx: llama_context_p,
    filepath: bytes,
    dest_seq_id: llama_seq_id,
    tokens_out: CtypesArray[llama_token],
    n_token_capacity: Union[ctypes.c_size_t, int],
    n_token_count_out: CtypesPointerOrRef[ctypes.c_size_t],
    /,
) -> int:
    ...















@ctypes_function(
    "llama_batch_get_one",
    [
        llama_token_p,
        ctypes.c_int32,
    ],
    llama_batch,
)
def llama_batch_get_one(
    tokens: CtypesArray[llama_token],
    n_tokens: Union[ctypes.c_int, int],
    /,
) -> llama_batch:
    """Return batch for single sequence of tokens

    NOTE: this is a helper function to facilitate transition to the new batch API - avoid using it
    """
    ...













@ctypes_function(
    "llama_batch_init", [ctypes.c_int32, ctypes.c_int32, ctypes.c_int32], llama_batch
)
def llama_batch_init(
    n_tokens: Union[ctypes.c_int32, int],
    embd: Union[ctypes.c_int32, int],
    n_seq_max: Union[ctypes.c_int32, int],
    /,
) -> llama_batch:
    """Allocates a batch of tokens on the heap that can hold a maximum of n_tokens
    Each token can be assigned up to n_seq_max sequence ids
    The batch has to be freed with llama_batch_free()
    If embd != 0, llama_batch.embd will be allocated with size of n_tokens * embd * sizeof(float)
    Otherwise, llama_batch.token will be allocated to store n_tokens llama_token
    The rest of the llama_batch members are allocated with size n_tokens
    All members are left uninitialized"""
    ...




@ctypes_function("llama_batch_free", [llama_batch], None)
def llama_batch_free(batch: llama_batch, /):
    """Frees a batch of tokens allocated with llama_batch_init()"""
    ...











@ctypes_function("llama_encode", [llama_context_p_ctypes, llama_batch], ctypes.c_int32)
def llama_encode(ctx: llama_context_p, batch: llama_batch, /) -> int:
    """Process a batch of tokens using the encoder.
    0 - success
    < 0 - error"""
    ...

















@ctypes_function("llama_decode", [llama_context_p_ctypes, llama_batch], ctypes.c_int32)
def llama_decode(ctx: llama_context_p, batch: llama_batch, /) -> int:
    """Process a batch of tokens.
    0 - success
    1 - could not find a KV slot for the batch (try reducing the size of the batch or increase the context)
    2 - aborted (processed ubatches will remain in the context's memory)
    -1 - invalid input batch
    < -1 - fatal error (processed ubatches will remain in the context's memory)"""
    ...






@ctypes_function(
    "llama_set_n_threads",
    [
        llama_context_p_ctypes,
        ctypes.c_int32,
        ctypes.c_int32,
    ],
    None,
)
def llama_set_n_threads(
    ctx: llama_context_p,
    n_threads: Union[ctypes.c_int32, int],
    n_threads_batch: Union[ctypes.c_int32, int],
    /,
):
    """Set the number of threads used for decoding
    n_threads is the number of threads used for generation (single token)
    n_threads_batch is the number of threads used for prompt and batch processing (multiple tokens)
    """
    ...




@ctypes_function("llama_n_threads", [llama_context_p_ctypes], ctypes.c_int32)
def llama_n_threads(ctx: llama_context_p, /) -> int:
    """Get the number of threads used for generation of a single token"""
    ...




@ctypes_function("llama_n_threads_batch", [llama_context_p_ctypes], ctypes.c_int32)
def llama_n_threads_batch(ctx: llama_context_p, /) -> int:
    """Get the number of threads used for prompt and batch processing (multiple token)"""
    ...





@ctypes_function("llama_set_embeddings", [llama_context_p_ctypes, ctypes.c_bool], None)
def llama_set_embeddings(ctx: llama_context_p, embeddings: bool, /):
    """Set whether the context outputs embeddings or not"""
    ...





@ctypes_function("llama_set_causal_attn", [llama_context_p_ctypes, ctypes.c_bool], None)
def llama_set_causal_attn(ctx: llama_context_p, causal_attn: bool, /):
    """Set whether to use causal attention or not
    If set to true, the model will only attend to the past tokens"""
    ...





@ctypes_function("llama_set_warmup", [llama_context_p_ctypes, ctypes.c_bool], None)
def llama_set_warmup(ctx: llama_context_p, warmup: bool, /):
    """Set whether the model is in warmup mode or not
    If true, all model tensors are activated during llama_decode() to load and cache their weights."""
    ...




@ctypes_function(
    "llama_set_abort_callback",
    [llama_context_p_ctypes, ggml_abort_callback, ctypes.c_void_p],
    None,
)
def llama_set_abort_callback(
    ctx: llama_context_p,
    abort_callback: Callable[[ctypes.c_void_p], None],
    abort_callback_data: ctypes.c_void_p,
    /,
):
    """Set abort callback"""
    ...






@ctypes_function("llama_synchronize", [llama_context_p_ctypes], None)
def llama_synchronize(ctx: llama_context_p, /):
    """Wait until all computations are finished
    This is automatically done when using one of the functions below to obtain the computation results
    and is not necessary to call it explicitly in most cases"""
    ...









@ctypes_function(
    "llama_get_logits", [llama_context_p_ctypes], ctypes.POINTER(ctypes.c_float)
)
def llama_get_logits(ctx: llama_context_p, /) -> CtypesArray[ctypes.c_float]:
    """Token logits obtained from the last call to llama_decode()
    The logits for which llama_batch.logits[i] != 0 are stored contiguously
    in the order they have appeared in the batch.
    Rows: number of tokens for which llama_batch.logits[i] != 0
    Cols: n_vocab

    Returns:
        Pointer to the logits buffer of shape (n_tokens, n_vocab)"""
    ...







@ctypes_function(
    "llama_get_logits_ith",
    [llama_context_p_ctypes, ctypes.c_int32],
    ctypes.POINTER(ctypes.c_float),
)
def llama_get_logits_ith(
    ctx: llama_context_p, i: Union[ctypes.c_int32, int], /
) -> CtypesArray[ctypes.c_float]:
    """Logits for the ith token. Equivalent to:
    llama_get_logits(ctx) + i*n_vocab"""
    ...










@ctypes_function(
    "llama_get_embeddings", [llama_context_p_ctypes], ctypes.POINTER(ctypes.c_float)
)
def llama_get_embeddings(ctx: llama_context_p, /) -> CtypesArray[ctypes.c_float]:
    """Get the embeddings for the input
    shape: [n_embd] (1-dimensional)"""
    ...








@ctypes_function(
    "llama_get_embeddings_ith",
    [llama_context_p_ctypes, ctypes.c_int32],
    ctypes.POINTER(ctypes.c_float),
)
def llama_get_embeddings_ith(
    ctx: llama_context_p, i: Union[ctypes.c_int32, int], /
) -> CtypesArray[ctypes.c_float]:
    """Get the embeddings for the ith sequence
    llama_get_embeddings(ctx) + i*n_embd"""
    ...







@ctypes_function(
    "llama_get_embeddings_seq",
    [llama_context_p_ctypes, llama_seq_id],
    ctypes.POINTER(ctypes.c_float),
)
def llama_get_embeddings_seq(
    ctx: llama_context_p, seq_id: Union[llama_seq_id, int], /
) -> CtypesArray[ctypes.c_float]:
    """Get the embeddings for a sequence id
    Returns NULL if pooling_type is LLAMA_POOLING_TYPE_NONE
    shape: [n_embd] (1-dimensional)"""
    ...







@ctypes_function(
    "llama_vocab_get_text", [llama_vocab_p_ctypes, llama_token], ctypes.c_char_p
)
def llama_vocab_get_text(
    vocab: llama_vocab_p, token: Union[llama_token, int], /
) -> bytes:
    ...



@ctypes_function(
    "llama_vocab_get_score", [llama_vocab_p_ctypes, llama_token], ctypes.c_float
)
def llama_vocab_get_score(
    vocab: llama_vocab_p, token: Union[llama_token, int], /
) -> float:
    ...



@ctypes_function(
    "llama_vocab_get_attr", [llama_vocab_p_ctypes, llama_token], ctypes.c_int
)
def llama_vocab_get_attr(
    vocab: llama_vocab_p, token: Union[llama_token, int], /
) -> int:
    ...




@ctypes_function(
    "llama_vocab_is_eog", [llama_vocab_p_ctypes, llama_token], ctypes.c_bool
)
def llama_vocab_is_eog(vocab: llama_vocab_p, token: Union[llama_token, int], /) -> bool:
    """Check if the token is supposed to end generation (end-of-generation, eg. EOS, EOT, etc.)"""
    ...




@ctypes_function(
    "llama_vocab_is_control", [llama_vocab_p_ctypes, llama_token], ctypes.c_bool
)
def llama_vocab_is_control(
    vocab: llama_vocab_p, token: Union[llama_token, int], /
) -> bool:
    """Identify if Token Id is a control token or a render-able token"""
    ...




@ctypes_function("llama_vocab_bos", [llama_vocab_p_ctypes], llama_token)
def llama_vocab_bos(vocab: llama_vocab_p, /) -> llama_token:
    """beginning-of-sentence"""
    ...



@ctypes_function("llama_vocab_eos", [llama_vocab_p_ctypes], llama_token)
def llama_vocab_eos(vocab: llama_vocab_p, /) -> llama_token:
    """end-of-sentence"""
    ...



@ctypes_function("llama_vocab_eot", [llama_vocab_p_ctypes], llama_token)
def llama_vocab_eot(vocab: llama_vocab_p, /) -> llama_token:
    """end-of-turn"""
    ...



@ctypes_function("llama_vocab_sep", [llama_vocab_p_ctypes], llama_token)
def llama_vocab_sep(vocab: llama_vocab_p, /) -> llama_token:
    """sentence separator"""
    ...



@ctypes_function("llama_vocab_nl", [llama_vocab_p_ctypes], llama_token)
def llama_vocab_nl(vocab: llama_vocab_p, /) -> llama_token:
    """next-line"""
    ...



@ctypes_function("llama_vocab_pad", [llama_vocab_p_ctypes], llama_token)
def llama_vocab_pad(vocab: llama_vocab_p, /) -> llama_token:
    """padding"""
    ...



@ctypes_function("llama_vocab_mask", [llama_vocab_p_ctypes], llama_token)
def llama_vocab_mask(vocab: llama_vocab_p, /) -> llama_token:
    """mask"""
    ...



@ctypes_function(
    "llama_vocab_get_add_bos",
    [llama_vocab_p_ctypes],
    ctypes.c_bool,
)
def llama_vocab_get_add_bos(vocab: llama_vocab_p, /) -> bool:
    ...



@ctypes_function(
    "llama_vocab_get_add_eos",
    [llama_vocab_p_ctypes],
    ctypes.c_bool,
)
def llama_vocab_get_add_eos(vocab: llama_vocab_p, /) -> bool:
    ...



@ctypes_function(
    "llama_vocab_get_add_sep",
    [llama_vocab_p_ctypes],
    ctypes.c_bool,
)
def llama_vocab_get_add_sep(vocab: llama_vocab_p, /) -> bool:
    ...



@ctypes_function(
    "llama_vocab_fim_pre",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_vocab_fim_pre(vocab: llama_vocab_p, /) -> llama_token:
    ...



@ctypes_function(
    "llama_vocab_fim_suf",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_vocab_fim_suf(vocab: llama_vocab_p, /) -> llama_token:
    ...



@ctypes_function(
    "llama_vocab_fim_mid",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_vocab_fim_mid(vocab: llama_vocab_p, /) -> llama_token:
    ...



@ctypes_function(
    "llama_vocab_fim_pad",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_vocab_fim_pad(vocab: llama_vocab_p, /) -> llama_token:
    ...



@ctypes_function(
    "llama_vocab_fim_rep",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_vocab_fim_rep(vocab: llama_vocab_p, /) -> llama_token:
    ...



@ctypes_function(
    "llama_vocab_fim_sep",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_vocab_fim_sep(vocab: llama_vocab_p, /) -> llama_token:
    ...




@ctypes_function(
    "llama_token_get_text",
    [llama_vocab_p_ctypes, llama_token],
    ctypes.c_char_p,
)
def llama_token_get_text(
    vocab: llama_vocab_p, token: Union[llama_token, int], /
) -> bytes:
    ...



@ctypes_function(
    "llama_token_get_score",
    [llama_vocab_p_ctypes, llama_token],
    ctypes.c_float,
)
def llama_token_get_score(
    vocab: llama_vocab_p, token: Union[llama_token, int], /
) -> float:
    ...


@ctypes_function(
    "llama_token_get_attr",
    [llama_vocab_p_ctypes, llama_token],
    ctypes.c_int,
)
def llama_token_get_attr(
    vocab: llama_vocab_p, token: Union[llama_token, int], /
) -> int:
    ...


@ctypes_function(
    "llama_token_is_eog",
    [llama_vocab_p_ctypes, llama_token],
    ctypes.c_bool,
)
def llama_token_is_eog(
    vocab: llama_vocab_p, token: Union[llama_token, int], /
) -> bool:
    ...


@ctypes_function(
    "llama_token_is_control",
    [llama_vocab_p_ctypes, llama_token],
    ctypes.c_bool,
)
def llama_token_is_control(
    vocab: llama_vocab_p, token: Union[llama_token, int], /
) -> bool:
    ...


@ctypes_function(
    "llama_token_bos",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_token_bos(vocab: llama_vocab_p, /) -> int:
    ...


@ctypes_function(
    "llama_token_eos",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_token_eos(vocab: llama_vocab_p, /) -> int:
    ...


@ctypes_function(
    "llama_token_eot",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_token_eot(vocab: llama_vocab_p, /) -> int:
    ...


@ctypes_function(
    "llama_token_cls",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_token_cls(vocab: llama_vocab_p, /) -> int:
    ...


@ctypes_function(
    "llama_token_sep",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_token_sep(vocab: llama_vocab_p, /) -> int:
    ...



@ctypes_function(
    "llama_token_nl",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_token_nl(vocab: llama_vocab_p, /) -> int:
    ...



@ctypes_function(
    "llama_token_pad",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_token_pad(vocab: llama_vocab_p, /) -> int:
    ...



@ctypes_function(
    "llama_add_bos_token",
    [llama_vocab_p_ctypes],
    ctypes.c_bool,
)
def llama_add_bos_token(vocab: llama_vocab_p, /) -> bool:
    ...


@ctypes_function(
    "llama_add_eos_token",
    [llama_vocab_p_ctypes],
    ctypes.c_bool,
)
def llama_add_eos_token(vocab: llama_vocab_p, /) -> bool:
    ...



@ctypes_function(
    "llama_token_fim_pre",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_token_fim_pre(vocab: llama_vocab_p, /) -> llama_token:
    ...


@ctypes_function(
    "llama_token_fim_suf",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_token_fim_suf(vocab: llama_vocab_p, /) -> llama_token:
    ...


@ctypes_function(
    "llama_token_fim_mid",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_token_fim_mid(vocab: llama_vocab_p, /) -> llama_token:
    ...


@ctypes_function(
    "llama_token_fim_pad",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_token_fim_pad(vocab: llama_vocab_p, /) -> llama_token:
    ...


@ctypes_function(
    "llama_token_fim_rep",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_token_fim_rep(vocab: llama_vocab_p, /) -> llama_token:
    ...


@ctypes_function(
    "llama_token_fim_sep",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_token_fim_sep(vocab: llama_vocab_p, /) -> llama_token:
    ...




@ctypes_function(
    "llama_vocab_cls",
    [llama_vocab_p_ctypes],
    llama_token,
)
def llama_vocab_cls(vocab: llama_vocab_p, /) -> llama_token:
    ...
























@ctypes_function(
    "llama_tokenize",
    [
        llama_vocab_p_ctypes,
        ctypes.c_char_p,
        ctypes.c_int32,
        llama_token_p,
        ctypes.c_int32,
        ctypes.c_bool,
        ctypes.c_bool,
    ],
    ctypes.c_int32,
)
def llama_tokenize(
    vocab: llama_vocab_p,
    text: bytes,
    text_len: Union[ctypes.c_int, int],
    tokens: CtypesArray[llama_token],
    n_tokens_max: Union[ctypes.c_int, int],
    add_special: Union[ctypes.c_bool, bool],
    parse_special: Union[ctypes.c_bool, bool],
    /,
) -> int:
    """Convert the provided text into tokens.

    Args:
        vocab: The vocabulary to use for tokenization.
        text: The text to tokenize.
        text_len: The length of the text.
        tokens: The tokens pointer must be large enough to hold the resulting tokens.
        n_max_tokens: The maximum number of tokens to return.
        add_special: Allow adding special tokens if the model is configured to do so.
        parse_special: Allow parsing special tokens.

    Returns:
        Returns the number of tokens on success, no more than n_tokens_max
        Returns a negative number on failure - the number of tokens that would have been returned
    """
    ...














@ctypes_function(
    "llama_token_to_piece",
    [
        llama_vocab_p_ctypes,
        llama_token,
        ctypes.c_char_p,
        ctypes.c_int32,
        ctypes.c_int32,
        ctypes.c_bool,
    ],
    ctypes.c_int32,
)
def llama_token_to_piece(
    vocab: llama_vocab_p,
    token: Union[llama_token, int],
    buf: Union[ctypes.c_char_p, bytes, CtypesArray[ctypes.c_char]],
    length: Union[ctypes.c_int, int],
    lstrip: Union[ctypes.c_int, int],
    special: Union[ctypes.c_bool, bool],
    /,
) -> int:
    """Token Id -> Piece.
    Uses the vocabulary in the provided context.
    Does not write null terminator to the buffer.
    User code is responsible to remove the leading whitespace of the first non-BOS token when decoding multiple tokens.

    Args:
        vocab: The vocabulary to use for tokenization.
        token: The token to convert.
        buf: The buffer to write the token to.
        length: The length of the buffer.
        lstrip: The number of leading spaces to skip.
        special: If true, special tokens are rendered in the output."""
    ...
















@ctypes_function(
    "llama_detokenize",
    [
        llama_vocab_p_ctypes,
        ctypes.POINTER(llama_token),
        ctypes.c_int32,
        ctypes.c_char_p,
        ctypes.c_int32,
        ctypes.c_bool,
        ctypes.c_bool,
    ],
    ctypes.c_int32,
)
def llama_detokenize(
    vocab: llama_vocab_p,
    tokens: CtypesArray[llama_token],
    n_tokens: Union[ctypes.c_int, int],
    text: bytes,
    text_len_max: Union[ctypes.c_int, int],
    remove_special: Union[ctypes.c_bool, bool],
    unparse_special: Union[ctypes.c_bool, bool],
    /,
) -> int:
    """Convert the provided tokens into text (inverse of llama_tokenize()).

    Args:
        vocab: The vocabulary to use for tokenization.
        tokens: The tokens to convert.
        n_tokens: The number of tokens.
        text: The buffer to write the text to.
        text_len_max: The length of the buffer.
        remove_special: Allow to remove BOS and EOS tokens if model is configured to do so.
        unparse_special: If true, special tokens are rendered in the output."""
    ...























@ctypes_function(
    "llama_chat_apply_template",
    [
        ctypes.c_char_p,
        ctypes.POINTER(llama_chat_message),
        ctypes.c_size_t,
        ctypes.c_bool,
        ctypes.c_char_p,
        ctypes.c_int32,
    ],
    ctypes.c_int32,
)
def llama_chat_apply_template(
    tmpl: bytes,
    chat: CtypesArray[llama_chat_message],
    n_msg: int,
    add_ass: bool,
    buf: bytes,
    length: int,
    /,
) -> int:
    """Apply chat template.

    Args:
        tmpl: Template to use. If None, uses model's default
        chat: Array of chat messages
        n_msg: Number of messages
        add_ass: Whether to end prompt with assistant token
        buf: Output buffer
        length: Buffer length

    Returns:
        Number of bytes written, or needed if buffer too small
    """
    ...




@ctypes_function(
    "llama_chat_builtin_templates",
    [
        ctypes.POINTER(ctypes.c_char_p),
        ctypes.c_size_t,
    ],
    ctypes.c_int32,
)
def llama_chat_builtin_templates(
    output: CtypesArray[bytes],
    len: Union[ctypes.c_size_t, int],
    /,
) -> int:
    """Get list of built-in chat templates.

    Args:
        output: Output buffer to store template names.
        len: Length of the output buffer.

    Returns:
        Number of templates available.
        Returns a negative number on error.
    """
    ...







llama_sampler_context_t = ctypes.c_void_p














class llama_sampler_i(ctypes.Structure):
    ...






class llama_sampler(ctypes.Structure):
    _fields_ = [
        ("iface", ctypes.POINTER(llama_sampler_i)),
        ("ctx", llama_sampler_context_t),
    ]


if TYPE_CHECKING:
    llama_sampler_p = CtypesPointer[llama_sampler]

llama_sampler_p_ctypes = ctypes.POINTER(llama_sampler)

llama_sampler_i_name = ctypes.CFUNCTYPE(ctypes.c_char_p, llama_sampler_p_ctypes)
llama_sampler_i_accept = ctypes.CFUNCTYPE(None, llama_sampler_p_ctypes, llama_token)
llama_sampler_i_apply = ctypes.CFUNCTYPE(
    None, llama_sampler_p_ctypes, llama_token_data_array_p
)
llama_sampler_i_reset = ctypes.CFUNCTYPE(None, llama_sampler_p_ctypes)
llama_sampler_i_clone = ctypes.CFUNCTYPE(llama_sampler_p_ctypes, llama_sampler_p_ctypes)
llama_sampler_i_free = ctypes.CFUNCTYPE(None, llama_sampler_p_ctypes)

llama_sampler_i._fields_ = [
    ("name", llama_sampler_i_name),
    ("accept", llama_sampler_i_accept),
    ("apply", llama_sampler_i_apply),
    ("reset", llama_sampler_i_reset),
    ("clone", llama_sampler_i_clone),
    ("free", llama_sampler_i_free),
]




@ctypes_function(
    "llama_sampler_init",
    [ctypes.POINTER(llama_sampler_i), llama_sampler_context_t],
    llama_sampler_p_ctypes,
)
def llama_sampler_init(
    iface: ctypes.POINTER(llama_sampler_i), ctx: llama_sampler_context_t, /
) -> llama_sampler_p:
    ...



@ctypes_function(
    "llama_sampler_name",
    [llama_sampler_p_ctypes],
    ctypes.c_char_p,
)
def llama_sampler_name(smpl: llama_sampler_p, /) -> bytes:
    ...



@ctypes_function(
    "llama_sampler_accept",
    [llama_sampler_p_ctypes, llama_token],
    None,
)
def llama_sampler_accept(smpl: llama_sampler_p, token: Union[llama_token, int], /):
    ...



@ctypes_function(
    "llama_sampler_apply",
    [llama_sampler_p_ctypes, llama_token_data_array_p],
    None,
)
def llama_sampler_apply(
    smpl: llama_sampler_p, cur_p: CtypesArray[llama_token_data_array], /
):
    ...



@ctypes_function(
    "llama_sampler_reset",
    [llama_sampler_p_ctypes],
    None,
)
def llama_sampler_reset(smpl: llama_sampler_p, /):
    ...



@ctypes_function(
    "llama_sampler_clone",
    [llama_sampler_p_ctypes],
    llama_sampler_p_ctypes,
)
def llama_sampler_clone(smpl: llama_sampler_p, /) -> llama_sampler_p:
    ...




@ctypes_function(
    "llama_sampler_free",
    [llama_sampler_p_ctypes],
    None,
)
def llama_sampler_free(smpl: llama_sampler_p, /):
    ...






@ctypes_function(
    "llama_sampler_chain_init",
    [llama_sampler_chain_params],
    llama_sampler_p_ctypes,
)
def llama_sampler_chain_init(params: llama_sampler_chain_params, /) -> llama_sampler_p:
    ...




@ctypes_function(
    "llama_sampler_chain_add",
    [llama_sampler_p_ctypes, llama_sampler_p_ctypes],
    None,
)
def llama_sampler_chain_add(chain: llama_sampler_p, smpl: llama_sampler_p, /):
    ...



@ctypes_function(
    "llama_sampler_chain_get",
    [llama_sampler_p_ctypes, ctypes.c_int32],
    llama_sampler_p_ctypes,
)
def llama_sampler_chain_get(
    chain: llama_sampler_p, i: Union[ctypes.c_int32, int], /
) -> llama_sampler_p:
    ...



@ctypes_function(
    "llama_sampler_chain_n",
    [llama_sampler_p_ctypes],
    ctypes.c_int,
)
def llama_sampler_chain_n(chain: llama_sampler_p, /) -> int:
    ...




@ctypes_function(
    "llama_sampler_chain_remove",
    [llama_sampler_p_ctypes, ctypes.c_int32],
    llama_sampler_p_ctypes,
)
def llama_sampler_chain_remove(
    chain: llama_sampler_p, i: Union[ctypes.c_int32, int], /
) -> llama_sampler_p:
    ...





@ctypes_function("llama_sampler_init_greedy", [], llama_sampler_p_ctypes)
def llama_sampler_init_greedy() -> llama_sampler_p:
    ...



@ctypes_function("llama_sampler_init_dist", [ctypes.c_uint32], llama_sampler_p_ctypes)
def llama_sampler_init_dist(seed: int) -> llama_sampler_p:
    ...






@ctypes_function("llama_sampler_init_softmax", [], llama_sampler_p_ctypes)
def llama_sampler_init_softmax() -> llama_sampler_p:
    ...





@ctypes_function("llama_sampler_init_top_k", [ctypes.c_int32], llama_sampler_p_ctypes)
def llama_sampler_init_top_k(k: int) -> llama_sampler_p:
    ...




@ctypes_function(
    "llama_sampler_init_top_p",
    [ctypes.c_float, ctypes.c_size_t],
    llama_sampler_p_ctypes,
)
def llama_sampler_init_top_p(p: float, min_keep: int) -> llama_sampler_p:
    ...




@ctypes_function(
    "llama_sampler_init_min_p",
    [ctypes.c_float, ctypes.c_size_t],
    llama_sampler_p_ctypes,
)
def llama_sampler_init_min_p(p: float, min_keep: int) -> llama_sampler_p:
    ...




@ctypes_function(
    "llama_sampler_init_typical",
    [ctypes.c_float, ctypes.c_size_t],
    llama_sampler_p_ctypes,
)
def llama_sampler_init_typical(p: float, min_keep: int) -> llama_sampler_p:
    ...




@ctypes_function("llama_sampler_init_temp", [ctypes.c_float], llama_sampler_p_ctypes)
def llama_sampler_init_temp(t: float) -> llama_sampler_p:
    ...




@ctypes_function(
    "llama_sampler_init_temp_ext",
    [ctypes.c_float, ctypes.c_float, ctypes.c_float],
    llama_sampler_p_ctypes,
)
def llama_sampler_init_temp_ext(
    t: float, delta: float, exponent: float
) -> llama_sampler_p:
    ...




@ctypes_function(
    "llama_sampler_init_xtc",
    [ctypes.c_float, ctypes.c_float, ctypes.c_size_t, ctypes.c_uint32],
    llama_sampler_p_ctypes,
)
def llama_sampler_init_xtc(
    p: float, t: float, min_keep: int, seed: int, /
) -> llama_sampler_p:
    ...




@ctypes_function(
    "llama_sampler_init_top_n_sigma",
    [ctypes.c_float],
    llama_sampler_p_ctypes,
)
def llama_sampler_init_top_n_sigma(n: float, /) -> llama_sampler_p:
    ...









@ctypes_function(
    "llama_sampler_init_mirostat",
    [ctypes.c_int32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_int32],
    llama_sampler_p_ctypes,
)
def llama_sampler_init_mirostat(
    n_vocab: int, seed: int, tau: float, eta: float, m: int, /
) -> llama_sampler_p:
    ...







@ctypes_function(
    "llama_sampler_init_mirostat_v2",
    [ctypes.c_uint32, ctypes.c_float, ctypes.c_float],
    llama_sampler_p_ctypes,
)
def llama_sampler_init_mirostat_v2(
    seed: int, tau: float, eta: float, /
) -> llama_sampler_p:
    ...







@ctypes_function(
    "llama_sampler_init_grammar",
    [llama_vocab_p_ctypes, ctypes.c_char_p, ctypes.c_char_p],
    llama_sampler_p_ctypes,
)
def llama_sampler_init_grammar(
    vocab: llama_vocab_p, grammar_str: bytes, grammar_root: bytes, /
) -> llama_sampler_p:
    ...











@ctypes_function(
    "llama_sampler_init_grammar_lazy",
    [
        llama_vocab_p_ctypes,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_char_p),
        ctypes.c_size_t,
        ctypes.POINTER(llama_token),
        ctypes.c_size_t,
    ],
    llama_sampler_p_ctypes,
)
def llama_sampler_init_grammar_lazy(
    vocab: llama_vocab_p,
    grammar_str: bytes,
    grammar_root: bytes,
    trigger_words: CtypesArray[bytes],
    num_trigger_words: int,
    trigger_tokens: CtypesArray[llama_token],
    num_trigger_tokens: int,
    /,
) -> llama_sampler_p:
    ...











@ctypes_function(
    "llama_sampler_init_grammar_lazy_patterns",
    [
        llama_vocab_p_ctypes,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_char_p),
        ctypes.c_size_t,
        ctypes.POINTER(llama_token),
        ctypes.c_size_t,
    ],
    llama_sampler_p_ctypes,
)
def llama_sampler_init_grammar_lazy_patterns(
    vocab: llama_vocab_p,
    grammar_str: bytes,
    grammar_root: bytes,
    trigger_patterns: CtypesArray[bytes],
    num_trigger_patterns: int,
    trigger_tokens: CtypesArray[llama_token],
    num_trigger_tokens: int,
    /,
) -> llama_sampler_p:
    ...








@ctypes_function(
    "llama_sampler_init_penalties",
    [ctypes.c_int32, ctypes.c_float, ctypes.c_float, ctypes.c_float],
    llama_sampler_p_ctypes,
)
def llama_sampler_init_penalties(
    penalty_last_n: int,
    penalty_repeat: float,
    penalty_freq: float,
    penalty_present: float,
    /,
) -> llama_sampler_p:
    ...












@ctypes_function(
    "llama_sampler_init_dry",
    [
        llama_vocab_p_ctypes,
        ctypes.c_int32,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_int32,
        ctypes.c_int32,
        ctypes.POINTER(ctypes.c_char_p),
        ctypes.c_size_t,
    ],
    llama_sampler_p_ctypes,
)
def llama_sampler_init_dry(
    vocab: llama_vocab_p,
    n_ctx_train: int,
    dry_multiplier: float,
    dry_base: float,
    dry_allowed_length: int,
    dry_penalty_last_n: int,
    seq_breakers,
    num_breakers: int,
    /,
) -> llama_sampler_p:
    ...






@ctypes_function(
    "llama_sampler_init_logit_bias",
    [ctypes.c_int32, ctypes.c_int32, llama_logit_bias_p],
    llama_sampler_p_ctypes,
)
def llama_sampler_init_logit_bias(
    n_vocab: int, n_logit_bias: int, logit_bias: CtypesArray[llama_logit_bias], /
) -> llama_sampler_p:
    ...




@ctypes_function(
    "llama_sampler_init_infill",
    [llama_vocab_p_ctypes],
    llama_sampler_p_ctypes,
)
def llama_sampler_init_infill(vocab: llama_vocab_p, /) -> llama_sampler_p:
    ...




@ctypes_function(
    "llama_sampler_get_seed",
    [llama_sampler_p_ctypes],
    ctypes.c_uint32,
)
def llama_sampler_get_seed(smpl: llama_sampler_p, /) -> int:
    ...




@ctypes_function(
    "llama_sampler_sample",
    [llama_sampler_p_ctypes, llama_context_p_ctypes, ctypes.c_int32],
    llama_token,
)
def llama_sampler_sample(
    smpl: llama_sampler_p, ctx: llama_context_p, idx: int, /
) -> int:
    ...








@ctypes_function(
    "llama_split_path",
    [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_int, ctypes.c_int],
    ctypes.c_int,
)
def llama_split_path(
    split_path: bytes,
    maxlen: Union[ctypes.c_size_t, int],
    path_prefix: bytes,
    split_no: Union[ctypes.c_int, int],
    split_count: Union[ctypes.c_int, int],
    /,
) -> int:
    """Build a split GGUF final path for this chunk."""
    ...




@ctypes_function(
    "llama_split_prefix",
    [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_int, ctypes.c_int],
    ctypes.c_int,
)
def llama_split_prefix(
    split_prefix: bytes,
    maxlen: Union[ctypes.c_size_t, int],
    split_path: bytes,
    split_no: Union[ctypes.c_int, int],
    split_count: Union[ctypes.c_int, int],
    /,
) -> int:
    """Extract the path prefix from the split_path if and only if the split_no and split_count match."""
    ...




@ctypes_function("llama_print_system_info", [], ctypes.c_char_p)
def llama_print_system_info() -> bytes:
    ...





@ctypes_function(
    "llama_log_set",
    [ctypes.c_void_p, ctypes.c_void_p],
    None,
)
def llama_log_set(
    log_callback: Optional[CtypesFuncPointer],
    user_data: ctypes.c_void_p,
    /,
):
    """Set callback for all future logging events.

    If this is not called, or NULL is supplied, everything is output on stderr."""
    ...
















class llama_perf_context_data(ctypes.Structure):
    _fields_ = [
        ("t_start_ms", ctypes.c_double),
        ("t_load_ms", ctypes.c_double),
        ("t_p_eval_ms", ctypes.c_double),
        ("t_eval_ms", ctypes.c_double),
        ("n_p_eval", ctypes.c_int32),
        ("n_eval", ctypes.c_int32),
        ("n_reused", ctypes.c_int32),
    ]







class llama_perf_sampler_data(ctypes.Structure):
    _fields_ = [
        ("t_sample_ms", ctypes.c_double),
        ("n_sample", ctypes.c_int32),
    ]



@ctypes_function(
    "llama_perf_context",
    [llama_context_p_ctypes],
    llama_perf_context_data,
)
def llama_perf_context(ctx: llama_context_p, /) -> llama_perf_context_data:
    ...



@ctypes_function(
    "llama_perf_context_print",
    [llama_context_p_ctypes],
    None,
)
def llama_perf_context_print(ctx: llama_context_p, /):
    ...



@ctypes_function(
    "llama_perf_context_reset",
    [llama_context_p_ctypes],
    None,
)
def llama_perf_context_reset(ctx: llama_context_p, /):
    ...




@ctypes_function(
    "llama_perf_sampler",
    [llama_sampler_p_ctypes],
    llama_perf_sampler_data,
)
def llama_perf_sampler(chain: llama_sampler_p, /) -> llama_perf_sampler_data:
    ...



@ctypes_function(
    "llama_perf_sampler_print",
    [llama_sampler_p_ctypes],
    None,
)
def llama_perf_sampler_print(chain: llama_sampler_p, /):
    ...



@ctypes_function(
    "llama_perf_sampler_reset",
    [llama_sampler_p_ctypes],
    None,
)
def llama_perf_sampler_reset(chain: llama_sampler_p, /):
    ...








llama_opt_param_filter = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)



@ctypes_function(
    "llama_opt_param_filter_all",
    [ctypes.c_void_p, ctypes.c_void_p],
    ctypes.c_bool,
)
def llama_opt_param_filter_all(tensor: ctypes.c_void_p, userdata: ctypes.c_void_p, /) -> bool:
    ...











class llama_opt_params(ctypes.Structure):
    _fields_ = [
        ("n_ctx_train", ctypes.c_uint32),
        ("param_filter", llama_opt_param_filter),
        ("param_filter_ud", ctypes.c_void_p),
        ("get_opt_pars", ctypes.c_void_p),
        ("get_opt_pars_ud", ctypes.c_void_p),
    ]



@ctypes_function(
    "llama_opt_init",
    [llama_context_p_ctypes, llama_model_p_ctypes, llama_opt_params],
    None,
)
def llama_opt_init(lctx: llama_context_p, model: llama_model_p, lopt_params: llama_opt_params, /):
    ...










@ctypes_function(
    "llama_opt_epoch",
    [
        llama_context_p_ctypes,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_int64,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ],
    None,
)
def llama_opt_epoch(
    lctx: llama_context_p,
    dataset: ctypes.c_void_p,
    result_train: ctypes.c_void_p,
    result_eval: ctypes.c_void_p,
    idata_split: int,
    callback_train: ctypes.c_void_p,
    callback_eval: ctypes.c_void_p,
    /,
):
    ...
