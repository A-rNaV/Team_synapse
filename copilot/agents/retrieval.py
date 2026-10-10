"""One hybrid path: BM25 top-10, vector top-10, then a local cross-encoder rerank.

The matrix-row section is always kept. Chunk ids stay file.md#section.
"""

from __future__ import annotations

import hashlib
import threading
import time

from copilot import config, trace
from copilot.kb import get_chunk, load_chunks, search
from copilot.schemas import Chunk, Retrieval

# Logits from bge-reranker-base. Only a clearly unrelated query falls through.
MIN_RERANK_LOGIT = -4.0
_CHROMA = None
_CHROMA_HASH = ""
_CHROMA_LOCK = threading.Lock()

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
    try:
        return _hybrid(query, forced)
    except Exception:
        return _lexical(query, forced)


def _hybrid(query: str, forced: list[str]) -> Retrieval:
    from copilot.embed import encode, rerank

    candidates = _candidate_map(query, forced)
    ordered = list(candidates.values())
    passages = [chunk.text for chunk, _origin in ordered]
    logits = rerank(query, passages)
    scored = []
    for (chunk, origin), logit in zip(ordered, logits):
        scored.append({"id": chunk.id, "origin": origin, "rerank": round(logit, 4)})
    scored.sort(key=lambda item: item["rerank"], reverse=True)
    passing = [item for item in scored if item["rerank"] >= MIN_RERANK_LOGIT]
    keep_ids = [item["id"] for item in passing[:5]]
    for chunk_id in forced:
        if chunk_id and chunk_id not in keep_ids and get_chunk(chunk_id) is not None:
            keep_ids.append(chunk_id)
    chunks = [get_chunk(chunk_id) for chunk_id in keep_ids]
    chunks = [chunk for chunk in chunks if chunk is not None]
    best = scored[0]["rerank"] if scored else MIN_RERANK_LOGIT - 1
    return Retrieval(query=query, chunks=chunks, weak=best < MIN_RERANK_LOGIT, scores=scored[:10])


def _candidate_map(query: str, forced: list[str]) -> dict[str, tuple[Chunk, str]]:
    found: dict[str, tuple[Chunk, str]] = {}
    for chunk, _score in search(query, k=10):
        found.setdefault(chunk.id, (chunk, "bm25"))
    for chunk in _vector_hits(query, 10):
        if chunk.id in found:
            origin = found[chunk.id][1]
            found[chunk.id] = (chunk, origin if origin == "bm25" else "vector")
            if origin == "bm25":
                found[chunk.id] = (chunk, "both")
        else:
            found[chunk.id] = (chunk, "vector")
    for chunk_id in forced:
        chunk = get_chunk(chunk_id)
        if chunk is None:
            continue
        if chunk.id not in found:
            found[chunk.id] = (chunk, "forced")
    return found


def _vector_hits(query: str, k: int) -> list[Chunk]:
    from copilot.embed import encode

    collection = _collection()
    vector = encode([query])[0].tolist()
    result = collection.query(query_embeddings=[vector], n_results=k)
    ids = (result.get("ids") or [[]])[0]
    hits = []
    for chunk_id in ids:
        chunk = get_chunk(chunk_id)
        if chunk is not None:
            hits.append(chunk)
    return hits


def _collection():
    with _CHROMA_LOCK:
        return _collection_locked()


def _collection_locked():
    global _CHROMA, _CHROMA_HASH
    import chromadb

    chunks = load_chunks()
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk.id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(chunk.text.encode("utf-8"))
    current = digest.hexdigest()
    path = config.ROOT / ".chroma"
    path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(path))
    if _CHROMA is not None and _CHROMA_HASH == current:
        return _CHROMA
    existing = {item.name for item in client.list_collections()}
    if "kb_chunks" in existing and _read_hash(path) != current:
        client.delete_collection("kb_chunks")
    collection = client.get_or_create_collection(name="kb_chunks", metadata={"hnsw:space": "cosine"})
    if collection.count() != len(chunks):
        from copilot.embed import encode

        vectors = encode([f"{chunk.heading}\n{chunk.text}" for chunk in chunks])
        collection.upsert(
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=vectors.tolist(),
        )
        (path / "kb_hash.txt").write_text(current, encoding="utf-8")
    _CHROMA = collection
    _CHROMA_HASH = current
    return collection


def _read_hash(path) -> str:
    hash_path = path / "kb_hash.txt"
    if not hash_path.is_file():
        return ""
    return hash_path.read_text(encoding="utf-8").strip()


def _lexical(query: str, forced: list[str]) -> Retrieval:
    chunks = []
    seen = set()
    for chunk_id in forced:
        chunk = get_chunk(chunk_id)
        if chunk is None or chunk.id in seen:
            continue
        seen.add(chunk.id)
        chunks.append(chunk)
    room = max(config.MAX_CHUNKS - len(chunks), 0)
    extra_budget = min(config.BM25_EXTRA_HITS, room)
    if extra_budget:
        for chunk, _score in search(query, k=extra_budget + len(seen)):
            if chunk.id in seen:
                continue
            seen.add(chunk.id)
            chunks.append(chunk)
            if len(chunks) >= len(forced) + extra_budget:
                break
    return Retrieval(query=query, chunks=chunks[: config.MAX_CHUNKS], weak=False, scores=[])


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
