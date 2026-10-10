"""BM25 top-10 plus vector top-10, then the BGE cross-encoder.

The matrix-row section is always kept. Chunk ids stay file.md#section.
Policy vectors are cached in .cache/kb_emb.npy. A query whose best rerank
score is below the cutoff is weak and escalates.
"""

from __future__ import annotations

import hashlib
import threading
import time

import numpy as np

from copilot import config, trace
from copilot.kb import get_chunk, load_chunks, search
from copilot.schemas import Chunk, Retrieval

# bge-reranker-base emits logits. Zero is the usual relevant/irrelevant cut.
MIN_RERANK = 0.0
_KB_MATRIX: np.ndarray | None = None
_KB_HASH = ""
_KB_LOCK = threading.Lock()

_ANALYTICS = "01_retail_operations_sop.md#analytics-rule"
_PRIORITY = "01_retail_operations_sop.md#priority-rules"
_PII = "05_responsible_ai_policy.md#pii-and-payment-data-masking"
_INJECTION = "05_responsible_ai_policy.md#prompt-injection"
_PAYMENT = "02_pos_pricing_returns_policy.md#payment-security"
_APPROVAL = "05_responsible_ai_policy.md#human-in-the-loop"
_STOCK = "03_inventory_replenishment_policy.md#stock-outs-and-replenishment"
_ROOT = "03_inventory_replenishment_policy.md#root-cause-hints"
_SHORT = "04_vendor_quality_policy.md#short-shipments"
_VENDOR = "04_vendor_quality_policy.md#vendor-performance"
_QUALITY = "04_vendor_quality_policy.md#product-quality-complaints"
_RUNBOOK = "02_pos_pricing_returns_policy.md#pos-card-reader-runbook"
_PRICE = "02_pos_pricing_returns_policy.md#pricing-and-promotions"
_RETURNS = "02_pos_pricing_returns_policy.md#returns-and-refunds"


def gather(masked_text: str, triage: dict, safety: dict) -> Retrieval:
    forced = _required_ids(triage, safety)
    query = _expand_query(masked_text, triage, safety)
    candidates = _candidates(query, forced)
    ordered = list(candidates.values())
    from copilot.embed import rerank

    logits = rerank(query, [chunk.text for chunk, _origin in ordered])
    scored = []
    for (chunk, origin), logit in zip(ordered, logits):
        scored.append({"id": chunk.id, "origin": origin, "rerank": round(float(logit), 4)})
    scored.sort(key=lambda item: item["rerank"], reverse=True)
    passing = [item["id"] for item in scored if item["rerank"] >= MIN_RERANK][:5]
    keep_ids = list(passing)
    for chunk_id in forced:
        if chunk_id and chunk_id not in keep_ids and get_chunk(chunk_id) is not None:
            keep_ids.append(chunk_id)
    chunks = [chunk for chunk in (get_chunk(chunk_id) for chunk_id in keep_ids) if chunk is not None]
    best = scored[0]["rerank"] if scored else MIN_RERANK - 1
    return Retrieval(query=query, chunks=chunks, weak=best < MIN_RERANK, scores=scored[:10])


def _candidates(query: str, forced: list[str]) -> dict[str, tuple[Chunk, str]]:
    found: dict[str, tuple[Chunk, str]] = {}
    for chunk, _score in search(query, k=10):
        found[chunk.id] = (chunk, "bm25")
    for chunk, _score in _vector_hits(query, 10):
        if chunk.id in found:
            found[chunk.id] = (chunk, "both")
        else:
            found[chunk.id] = (chunk, "vector")
    for chunk_id in forced:
        chunk = get_chunk(chunk_id)
        if chunk is not None and chunk.id not in found:
            found[chunk.id] = (chunk, "forced")
    return found


def _vector_hits(query: str, k: int) -> list[tuple[Chunk, float]]:
    from copilot.embed import encode

    chunks = load_chunks()
    matrix = _kb_matrix(chunks)
    if matrix.size == 0:
        return []
    query_vector = encode([query], for_retrieval=True)[0]
    sims = matrix @ query_vector
    order = np.argsort(-sims)[:k]
    hits = []
    for index in order:
        score = float(sims[int(index)])
        if score <= 0:
            continue
        hits.append((chunks[int(index)], score))
    return hits


def _kb_matrix(chunks: list[Chunk]) -> np.ndarray:
    with _KB_LOCK:
        return _kb_matrix_locked(chunks)


def _kb_matrix_locked(chunks: list[Chunk]) -> np.ndarray:
    global _KB_MATRIX, _KB_HASH
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk.id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(chunk.text.encode("utf-8"))
    current = digest.hexdigest()
    if _KB_MATRIX is not None and _KB_HASH == current:
        return _KB_MATRIX
    path = config.ROOT / ".cache" / "kb_emb.npy"
    hash_path = config.ROOT / ".cache" / "kb_emb.sha"
    if path.is_file() and hash_path.is_file() and hash_path.read_text(encoding="utf-8").strip() == current:
        matrix = np.load(path)
    else:
        from copilot.embed import encode

        matrix = encode([f"{chunk.heading}\n{chunk.text}" for chunk in chunks])
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, matrix)
        hash_path.write_text(current, encoding="utf-8")
    _KB_MATRIX = matrix
    _KB_HASH = current
    return matrix


def retrieval_node(state: dict) -> dict:
    started = time.perf_counter()
    result = gather(
        state.get("masked_text") or "",
        state.get("triage") or {},
        state.get("safety") or {},
    )
    update = {"retrieval": result.model_dump()}
    update["trace"] = [
        trace.record(
            request_id=state.get("request_id", ""),
            agent="retrieval",
            mode="rule",
            started=started,
            input_summary=result.query,
            output_summary={
                "chunk_ids": [chunk.id for chunk in result.chunks],
                "weak": result.weak,
                "scores": result.scores,
            },
        )
    ]
    return update


def _required_ids(triage: dict, safety: dict) -> list[str]:
    ids = [triage.get("policy_source") or ""]
    if triage.get("priority") == "P1":
        ids.append(_PRIORITY)
    if triage.get("needs_data"):
        ids.append(_ANALYTICS)
    if safety.get("pii_masked"):
        ids.append(_PII)
    if safety.get("refusal"):
        ids.extend([_INJECTION, _PAYMENT])
    if triage.get("human_approval_required"):
        ids.append(_APPROVAL)
    intent = triage.get("intent") or ""
    if intent == "stock_root_cause":
        ids.extend([_STOCK, _ROOT, _SHORT, _VENDOR])
    elif intent == "vendor_quality_ranking":
        ids.extend([_VENDOR, _QUALITY])
    elif intent == "quality_trend":
        ids.append(_QUALITY)
    category = triage.get("category")
    if category == "POS and Payments":
        ids.append(_RUNBOOK)
    elif category == "Pricing and Promotions":
        ids.append(_PRICE)
    elif category == "Returns and Refunds":
        ids.append(_RETURNS)
    ordered = []
    for chunk_id in ids:
        if chunk_id and chunk_id not in ordered:
            ordered.append(chunk_id)
    return ordered


def _expand_query(masked_text: str, triage: dict, safety: dict) -> str:
    extra = [
        str(triage.get("category") or ""),
        str(triage.get("trigger") or ""),
        str(triage.get("policy_source") or "").replace("#", " ").replace("-", " "),
    ]
    if safety.get("refusal"):
        extra.append("prompt injection payment security card numbers")
    if triage.get("needs_data"):
        extra.append("analytics rule csv last 24 hours last 30 days")
    return (masked_text + " " + " ".join(extra)).strip()
