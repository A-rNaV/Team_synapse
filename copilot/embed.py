"""Same BGE models as the spec, via ONNX. No PyTorch and no vector database.

bge-small-en-v1.5 embeds cases and policy sections. bge-reranker-base scores
query/passage pairs. Vectors are cached under .cache/. DeepSeek stays the chat
fallback and is not used here: its API has no embeddings or rerank endpoint.
"""

from __future__ import annotations

import os
import threading

import numpy as np

from copilot.config import ROOT

ENCODER_NAME = "BAAI/bge-small-en-v1.5"
RERANKER_NAME = "BAAI/bge-reranker-base"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
CACHE_DIR = ROOT / ".cache" / "fastembed"

_LOCK = threading.Lock()
_ENCODER = None
_RERANKER = None


def encode(texts: list[str], *, for_retrieval: bool = False) -> np.ndarray:
    """Unit vectors. Cosine similarity is a dot product.

    Retrieval queries get the BGE passage prefix. Case-to-case kNN does not,
    because both sides are issue texts.
    """
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    prepared = [QUERY_PREFIX + text if for_retrieval else text for text in texts]
    model = _encoder()
    with _LOCK:
        rows = [np.asarray(vector, dtype=np.float32) for vector in model.embed(prepared)]
    matrix = np.vstack(rows)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.clip(norms, 1e-9, None)


def rerank(query: str, passages: list[str]) -> list[float]:
    """Cross-encoder scores in passage order. Higher means more relevant."""
    if not passages:
        return []
    model = _reranker()
    with _LOCK:
        raw = list(model.rerank(query, passages))
    scores = []
    for item in raw:
        value = getattr(item, "score", item)
        scores.append(float(value))
    return scores


def _encoder():
    global _ENCODER
    if _ENCODER is None:
        from fastembed import TextEmbedding

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("FASTEMBED_CACHE_PATH", str(CACHE_DIR))
        _ENCODER = TextEmbedding(model_name=ENCODER_NAME, cache_dir=str(CACHE_DIR))
    return _ENCODER


def _reranker():
    global _RERANKER
    if _RERANKER is None:
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("FASTEMBED_CACHE_PATH", str(CACHE_DIR))
        _RERANKER = TextCrossEncoder(model_name=RERANKER_NAME, cache_dir=str(CACHE_DIR))
    return _RERANKER
