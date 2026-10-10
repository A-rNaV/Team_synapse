"""Split each knowledge-base file on '##' headings and search them with BM25."""

from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

from copilot.config import KB_DIR
from copilot.schemas import Chunk

_CHUNKS: list[Chunk] | None = None
_BM25: BM25Okapi | None = None


def slug(heading: str) -> str:
    """Turn a heading into the citation slug used in public_test_cases.csv."""
    lowered = heading.strip().lower()
    dashed = re.sub(r"[^a-z0-9]+", "-", lowered)
    return dashed.strip("-")


def load_chunks() -> list[Chunk]:
    global _CHUNKS, _BM25
    if _CHUNKS is not None:
        return _CHUNKS
    chunks: list[Chunk] = []
    for path in sorted(KB_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        sections = re.split(r"(?m)^## ", raw)
        for section in sections[1:]:
            heading, _, body = section.partition("\n")
            heading = heading.strip()
            if not heading:
                continue
            text = f"{heading}\n{body.strip()}"
            chunks.append(
                Chunk(
                    id=f"{path.name}#{slug(heading)}",
                    source=path.name,
                    heading=heading,
                    text=text,
                )
            )
    _CHUNKS = chunks
    _BM25 = BM25Okapi([_tokens(chunk.text) for chunk in chunks])
    return chunks


def chunk_ids() -> list[str]:
    return [chunk.id for chunk in load_chunks()]


def get_chunk(chunk_id: str) -> Chunk | None:
    for chunk in load_chunks():
        if chunk.id == chunk_id:
            return chunk
    return None


def search(query: str, k: int = 4) -> list[tuple[Chunk, float]]:
    """Return up to k (chunk, score) pairs. Score 0 means no lexical overlap."""
    chunks = load_chunks()
    if _BM25 is None or not chunks:
        return []
    query_tokens = _tokens(query)
    if not query_tokens:
        return []
    scores = _BM25.get_scores(query_tokens)
    ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
    hits: list[tuple[Chunk, float]] = []
    for index, score in ranked[:k]:
        if score <= 0:
            continue
        hits.append((chunks[index], float(score)))
    return hits


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())
