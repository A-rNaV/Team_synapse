"""Local BAAI encoders, loaded once. The API model is not involved."""

from __future__ import annotations

import threading

import numpy as np

ENCODER_NAME = "BAAI/bge-small-en-v1.5"
RERANKER_NAME = "BAAI/bge-reranker-base"

_LOCK = threading.Lock()
_ENCODER = None
_RERANKER = None


def encode(texts: list[str]) -> np.ndarray:
    """Unit vectors. Cosine similarity is a dot product."""
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    model = _encoder()
    with _LOCK:
        vectors = model.encode(
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=False,
        )
    return np.asarray(vectors, dtype=np.float32)


def rerank(query: str, passages: list[str]) -> list[float]:
    """Cross-encoder logits. Higher means the passage is more relevant."""
    if not passages:
        return []
    model = _reranker()
    pairs = [(query, passage) for passage in passages]
    with _LOCK:
        scores = model.predict(pairs, show_progress_bar=False)
    return [float(score) for score in np.asarray(scores).reshape(-1)]


def _encoder():
    global _ENCODER
    if _ENCODER is None:
        from sentence_transformers import SentenceTransformer

        _ENCODER = SentenceTransformer(ENCODER_NAME)
    return _ENCODER


def _reranker():
    global _RERANKER
    if _RERANKER is None:
        from sentence_transformers import CrossEncoder

        _RERANKER = CrossEncoder(RERANKER_NAME)
    return _RERANKER
