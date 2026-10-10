"""Embedding kNN over labelled support cases.

Vectors come from BAAI/bge-small-en-v1.5 and are cached in .cache/case_emb.npy.
The cache rebuilds only when the CSV or the eval prompts change. Rows with
cosine above 0.95 to any eval prompt are left out of the index.
"""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass

import numpy as np
import pandas as pd

from copilot.config import DATA_DIR, EVAL_DIR, ROOT
from copilot.data import trigger_for_labels
from copilot.embed import encode

CACHE_DIR = ROOT / ".cache"
EMB_PATH = CACHE_DIR / "case_emb.npy"
META_PATH = CACHE_DIR / "case_meta.json"
HASH_PATH = CACHE_DIR / "case_index_hash.txt"
THRESHOLD_PATH = CACHE_DIR / "knn_thresholds.json"

TOP_K = 7
CONF_THRESHOLD = 0.75
SIM_THRESHOLD = 0.85

_INDEX: "KnnIndex | None" = None
_INDEX_LOCK = threading.Lock()


@dataclass
class KnnHit:
    trigger: str
    category: str
    priority: str
    confidence: float
    top1: float
    neighbours: list[dict]


@dataclass
class KnnIndex:
    matrix: np.ndarray
    rows: list[dict]
    conf_threshold: float
    sim_threshold: float


def thresholds() -> tuple[float, float]:
    index = load_index()
    return index.conf_threshold, index.sim_threshold


def lookup(text: str) -> KnnHit | None:
    index = load_index()
    if index.matrix.size == 0:
        return None
    query = encode([text])[0]
    return _vote(query, index.matrix, index.rows)


def load_index() -> KnnIndex:
    with _INDEX_LOCK:
        return _load_index_locked()


def _load_index_locked() -> KnnIndex:
    global _INDEX, CONF_THRESHOLD, SIM_THRESHOLD
    if _INDEX is not None:
        return _INDEX
    digest = _source_hash()
    cached = _read_cache(digest)
    if cached is None:
        cached = _build(digest)
    CONF_THRESHOLD = cached.conf_threshold
    SIM_THRESHOLD = cached.sim_threshold
    _INDEX = cached
    print(
        f"kNN thresholds: knn_conf>={cached.conf_threshold:.2f} "
        f"top1_similarity>={cached.sim_threshold:.2f}"
    )
    return cached


def _vote(query: np.ndarray, matrix: np.ndarray, rows: list[dict]) -> KnnHit | None:
    if len(rows) == 0:
        return None
    sims = matrix @ query
    k = min(TOP_K, len(rows))
    chosen = np.argpartition(-sims, k - 1)[:k]
    chosen = chosen[np.argsort(-sims[chosen])]
    row_weights: dict[str, float] = {}
    category_weights: dict[str, float] = {}
    neighbours = []
    for rank, index in enumerate(chosen):
        similarity = float(sims[int(index)])
        if similarity <= 0:
            continue
        row = rows[int(index)]
        row_weights[row["row"]] = row_weights.get(row["row"], 0.0) + similarity
        category_weights[row["category"]] = category_weights.get(row["category"], 0.0) + similarity
        if rank < 3:
            neighbours.append(
                {
                    "case_id": row["case_id"],
                    "text": row["text"],
                    "category": row["category"],
                    "priority": row["priority"],
                    "row": row["row"],
                    "store": row["store"],
                    "sku": row["sku"],
                    "similarity": round(similarity, 4),
                }
            )
    if not row_weights or not neighbours:
        return None
    trigger = max(row_weights, key=row_weights.get)
    category = max(category_weights, key=category_weights.get)
    row_share = row_weights[trigger] / sum(row_weights.values())
    category_share = category_weights[category] / sum(category_weights.values())
    top1 = float(neighbours[0]["similarity"])
    winner = next(row for row in rows if row["row"] == trigger)
    if winner["category"] != category:
        category = winner["category"]
    return KnnHit(
        trigger=trigger,
        category=category,
        priority=winner["priority"],
        confidence=float(min(row_share, category_share) * top1),
        top1=top1,
        neighbours=neighbours,
    )


def _build(digest: str) -> KnnIndex:
    cases = pd.read_csv(DATA_DIR / "support_cases.csv")
    prompts = _eval_prompts()
    issues = cases["issue_text"].fillna("").astype(str).tolist()
    prompt_matrix = encode(prompts) if prompts else np.zeros((0, 384), dtype=np.float32)
    issue_matrix = encode(issues)
    keep = []
    for index, issue_vector in enumerate(issue_matrix):
        if prompt_matrix.size and float(np.max(prompt_matrix @ issue_vector)) > 0.95:
            continue
        keep.append(index)
    rows = [_row(cases.iloc[index]) for index in keep]
    matrix = issue_matrix[keep]
    conf, sim = _tune(matrix, rows)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.save(EMB_PATH, matrix)
    META_PATH.write_text(json.dumps(rows), encoding="utf-8")
    HASH_PATH.write_text(digest, encoding="utf-8")
    THRESHOLD_PATH.write_text(
        json.dumps({"knn_conf": conf, "top1_similarity": sim}),
        encoding="utf-8",
    )
    return KnnIndex(matrix=matrix, rows=rows, conf_threshold=conf, sim_threshold=sim)


def _tune(matrix: np.ndarray, rows: list[dict]) -> tuple[float, float]:
    """Pick thresholds on a held-out 20% of support cases, never the eval suites."""
    holdout = [index for index, row in enumerate(rows) if _is_holdout(row["case_id"])]
    train = [index for index in range(len(rows)) if index not in set(holdout)]
    if len(holdout) < 5 or len(train) < 20:
        return CONF_THRESHOLD, SIM_THRESHOLD
    train_matrix = matrix[train]
    train_rows = [rows[index] for index in train]
    best = (CONF_THRESHOLD, SIM_THRESHOLD, -1.0)
    for conf in (0.65, 0.70, 0.75, 0.80, 0.85):
        for sim in (0.80, 0.85, 0.90):
            correct = 0
            for index in holdout:
                hit = _vote(matrix[index], train_matrix, train_rows)
                rules = _rules_for(rows[index]["text"])
                agrees = bool(hit and hit.category == rules[0] and hit.priority == rules[1])
                accepted = bool(hit) and hit.confidence >= conf and (agrees or hit.top1 >= sim)
                predicted = (hit.category, hit.priority) if accepted else rules
                if predicted == (rows[index]["category"], rows[index]["priority"]):
                    correct += 1
            accuracy = correct / len(holdout)
            rank = (accuracy, conf, sim)
            current = (best[2], best[0], best[1])
            if rank > current:
                best = (conf, sim, accuracy)
    print(
        f"kNN holdout accuracy at knn_conf>={best[0]:.2f} "
        f"top1>={best[1]:.2f}: {best[2]:.1%} on {len(holdout)} cases"
    )
    return best[0], best[1]


def _rules_for(text: str) -> tuple[str, str]:
    from copilot.agents.triage import classify_rules

    rules = classify_rules(text, {})
    return rules.category, rules.priority


def _is_holdout(case_id: str) -> bool:
    digest = hashlib.md5(case_id.encode("utf-8")).hexdigest()
    return int(digest[:2], 16) < 51


def _row(case) -> dict:
    issue = "" if _blank(case.issue_text) else str(case.issue_text)
    category = "" if _blank(case.category_label) else str(case.category_label)
    priority = "" if _blank(case.priority_label) else str(case.priority_label)
    return {
        "case_id": "" if _blank(case.case_id) else str(case.case_id),
        "text": issue,
        "category": category,
        "priority": priority,
        "row": trigger_for_labels(category, priority, issue),
        "store": "" if _blank(case.store_id) else str(case.store_id),
        "sku": "" if _blank(case.sku) else str(case.sku),
    }


def _read_cache(digest: str) -> KnnIndex | None:
    if not EMB_PATH.is_file() or not META_PATH.is_file() or not HASH_PATH.is_file():
        return None
    if HASH_PATH.read_text(encoding="utf-8").strip() != digest:
        return None
    matrix = np.load(EMB_PATH)
    rows = json.loads(META_PATH.read_text(encoding="utf-8"))
    conf, sim = CONF_THRESHOLD, SIM_THRESHOLD
    if THRESHOLD_PATH.is_file():
        payload = json.loads(THRESHOLD_PATH.read_text(encoding="utf-8"))
        conf = float(payload.get("knn_conf", conf))
        sim = float(payload.get("top1_similarity", sim))
    return KnnIndex(matrix=matrix, rows=rows, conf_threshold=conf, sim_threshold=sim)


def _source_hash() -> str:
    digest = hashlib.sha256()
    digest.update((DATA_DIR / "support_cases.csv").read_bytes())
    for prompt in _eval_prompts():
        digest.update(b"\0")
        digest.update(prompt.encode("utf-8"))
    digest.update(b"\0bge-small-en-v1.5")
    return digest.hexdigest()


def _eval_prompts() -> list[str]:
    prompts = []
    for path in sorted(EVAL_DIR.glob("*.csv")):
        if path.name.endswith("_cases.csv") or path.name == "public_test_cases.csv":
            frame = pd.read_csv(path)
            if "prompt" in frame.columns:
                prompts.extend(frame["prompt"].fillna("").astype(str).tolist())
    return prompts


def _blank(value) -> bool:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return True
    text = str(value).strip()
    return text == "" or text.lower() == "nan"
