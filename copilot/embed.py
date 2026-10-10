"""Same BGE models as the spec, via ONNX. No PyTorch and no vector database.

bge-small-en-v1.5 embeds cases and policy sections. bge-reranker-base scores
query/passage pairs. Vectors are cached under .cache/. DeepSeek stays the chat
fallback and is not used here: its API has no embeddings or rerank endpoint.

InferenceSession.run is thread-safe, so encode and rerank do not take a global
lock. Each session is limited to ONNX_THREADS so parallel workers do not
oversubscribe the CPU. Repeated queries reuse an in-process LRU cache.
"""

from __future__ import annotations

import os
import threading
from collections import OrderedDict

import numpy as np

from copilot.config import ONNX_THREADS, ROOT

ENCODER_NAME = "BAAI/bge-small-en-v1.5"
RERANKER_NAME = "BAAI/bge-reranker-base"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
CACHE_DIR = ROOT / ".cache" / "fastembed"
_CACHE_MAX = 2048

_INIT_LOCK = threading.Lock()
_CACHE_LOCK = threading.Lock()
_ENCODER = None
_RERANKER = None
_EMBED_CACHE: OrderedDict[tuple, np.ndarray] = OrderedDict()


def encode(texts: list[str], *, for_retrieval: bool = False) -> np.ndarray:
    """Unit vectors. Cosine similarity is a dot product.

    Retrieval queries get the BGE passage prefix. Case-to-case kNN does not,
    because both sides are issue texts.
    """
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    keys = [(for_retrieval, text) for text in texts]
    found: dict[int, np.ndarray] = {}
    missing: list[int] = []
    with _CACHE_LOCK:
        for index, key in enumerate(keys):
            cached = _EMBED_CACHE.get(key)
            if cached is None:
                missing.append(index)
            else:
                _EMBED_CACHE.move_to_end(key)
                found[index] = cached
    if missing:
        prepared = [QUERY_PREFIX + texts[index] if for_retrieval else texts[index] for index in missing]
        model = _encoder()
        fresh = [np.asarray(vector, dtype=np.float32) for vector in model.embed(prepared)]
        with _CACHE_LOCK:
            for index, vector in zip(missing, fresh):
                stored = np.array(vector, dtype=np.float32, copy=True)
                _remember(_EMBED_CACHE, keys[index], stored)
                found[index] = stored
    matrix = np.vstack([found[index] for index in range(len(texts))])
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.clip(norms, 1e-9, None)


def rerank(query: str, passages: list[str]) -> list[float]:
    """Cross-encoder scores in passage order. Higher means more relevant."""
    if not passages:
        return []
    model = _reranker()
    raw = list(model.rerank(query, passages))
    scores = []
    for item in raw:
        value = getattr(item, "score", item)
        scores.append(float(value))
    return scores


def _remember(cache: OrderedDict, key, value) -> None:
    cache[key] = value
    cache.move_to_end(key)
    while len(cache) > _CACHE_MAX:
        cache.popitem(last=False)


def _encoder():
    global _ENCODER
    if _ENCODER is None:
        with _INIT_LOCK:
            if _ENCODER is None:
                from fastembed import TextEmbedding

                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                os.environ.setdefault("FASTEMBED_CACHE_PATH", str(CACHE_DIR))
                _ENCODER = TextEmbedding(
                    model_name=ENCODER_NAME,
                    cache_dir=str(CACHE_DIR),
                    threads=ONNX_THREADS,
                )
    return _ENCODER


def _reranker():
    global _RERANKER
    if _RERANKER is None:
        with _INIT_LOCK:
            if _RERANKER is None:
                from fastembed.rerank.cross_encoder import TextCrossEncoder

                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                os.environ.setdefault("FASTEMBED_CACHE_PATH", str(CACHE_DIR))
                _RERANKER = TextCrossEncoder(
                    model_name=RERANKER_NAME,
                    cache_dir=str(CACHE_DIR),
                    threads=ONNX_THREADS,
                )
    return _RERANKER
