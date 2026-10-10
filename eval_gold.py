"""Gold strings for data-use checks. Every number is read from the CSVs at score time."""

from __future__ import annotations

from copilot.data import (
    load_frames,
    open_high_priority,
    quality_trend,
    short_shipments,
    stock_root_cause,
    vendor_quality_ranking,
)

PUBLIC_GOLD = {
    "PUB-003": "bat_root",
    "PUB-006": "seam_trend",
    "PUB-007": "open_window",
    "PUB-010": "vendor_rank",
    "PUB-011": "tennis_wh",
}


def requirements(gold_facts: str) -> tuple[list[str], list[str]]:
    """Return lowercase needles and the CSV names the answer must have used."""
    tokens = [part.strip() for part in str(gold_facts or "").split(";") if part.strip() and part.strip().lower() != "nan"]
    needles: list[str] = []
    files: list[str] = []
    for token in tokens:
        spec = _SPECS.get(token)
        if spec is None:
            needles.append(token.lower())
            continue
        needles.extend(spec["needles"]())
        files.extend(spec["files"])
    return _unique(needles), _unique(files)


def _open_needles() -> list[str]:
    result = open_high_priority(24)
    needles = [str(result["summary"]["total"]), "unresolved"]
    if any("ST003" in fact for fact in result["facts"]):
        needles.append("st003")
    return needles


def _bat_needles() -> list[str]:
    return _present(stock_root_cause("ST002", "SKU1001"), ["on_hand 0", "18 of 50", "0.68", "short"])


def _vendor_needles() -> list[str]:
    return _present(vendor_quality_ranking(30), ["v001", "jalandhar willow", "0.68"])


def _tennis_needles() -> list[str]:
    return _present(stock_root_cause("ST005", "SKU7001"), ["warehouse", "st005", "wh001"])


def _seam_needles() -> list[str]:
    return _present(quality_trend("SKU2003"), ["seam", "sku2003"])


def _short_needles() -> list[str]:
    return _present(short_shipments("V001", "SKU1001"), ["18 of 50", "short", "v001"])


def _worst_fill_needles() -> list[str]:
    vendors = load_frames()["vendor_master"].sort_values(["fill_rate", "vendor_id"])
    row = vendors.iloc[0]
    return [str(row["vendor_id"]).lower(), f"{float(row['fill_rate']):.2f}"]


def _multi_zero_needles() -> list[str]:
    inventory = load_frames()["inventory"]
    zero = inventory[inventory["on_hand"] == 0]
    counts = zero.groupby("sku").size()
    repeated = counts[counts >= 2]
    if repeated.empty:
        return ["on_hand 0"]
    sku = str(repeated.sort_values(ascending=False).index[0])
    stores = sorted(zero.loc[zero["sku"] == sku, "store_id"].astype(str).str.lower().unique())
    return [sku.lower(), *stores]


def _present(result: dict, candidates: list[str]) -> list[str]:
    blob = " ".join(result.get("facts") or []).lower()
    found = [item for item in candidates if item.lower() in blob]
    if found:
        return found
    facts = result.get("facts") or []
    return [facts[0][:48].lower()] if facts else candidates[:1]


def _unique(items: list[str]) -> list[str]:
    seen = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen


_SPECS = {
    "open_window": {"needles": _open_needles, "files": ["support_cases.csv"]},
    "bat_root": {
        "needles": _bat_needles,
        "files": ["inventory.csv", "receipts.csv", "vendor_master.csv"],
    },
    "vendor_rank": {
        "needles": _vendor_needles,
        "files": ["vendor_master.csv", "support_cases.csv", "returns_quality.csv"],
    },
    "tennis_wh": {
        "needles": _tennis_needles,
        "files": ["inventory.csv", "receipts.csv", "support_cases.csv"],
    },
    "seam_trend": {
        "needles": _seam_needles,
        "files": ["returns_quality.csv", "support_cases.csv"],
    },
    "short_ship": {"needles": _short_needles, "files": ["receipts.csv"]},
    "worst_fill": {"needles": _worst_fill_needles, "files": ["vendor_master.csv"]},
    "multi_zero": {"needles": _multi_zero_needles, "files": ["inventory.csv"]},
}
