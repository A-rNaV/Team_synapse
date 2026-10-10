"""Load the nine CSVs once and answer with pandas. No guessed numbers."""

from __future__ import annotations

import re

import pandas as pd

from copilot import config

_FRAMES: dict[str, pd.DataFrame] | None = None

FILES = [
    "support_cases",
    "product_master",
    "inventory",
    "store_master",
    "employee_master",
    "receipts",
    "vendor_master",
    "returns_quality",
    "escalation_matrix",
]

# Reasons that count as a sports-goods quality complaint. Packaging and size do not.
QUALITY_REASON = re.compile(
    r"quality|seam|split|defect|crack|unsafe|injury|belt slipped|lost air|malfunction",
    re.IGNORECASE,
)

_SKU_CODE = re.compile(r"\b(SKU\d{4})\b", re.IGNORECASE)
_STORE_CODE = re.compile(r"\b((?:ST|WH)\d{3})\b", re.IGNORECASE)
_GENERIC_TOKENS = {
    "junior",
    "senior",
    "pro",
    "club",
    "elite",
    "academy",
    "training",
    "tournament",
    "pack",
    "set",
    "size",
}
_NAME_INDEX: tuple[set[str], list[tuple[list[str], object]]] | None = None


def load_frames() -> dict[str, pd.DataFrame]:
    """Read every CSV under data/. employee_master is loaded and never displayed."""
    global _FRAMES
    if _FRAMES is not None:
        return _FRAMES
    frames: dict[str, pd.DataFrame] = {}
    for name in FILES:
        frames[name] = pd.read_csv(config.DATA_DIR / f"{name}.csv")
    frames["support_cases"]["created_ts"] = pd.to_datetime(frames["support_cases"]["created_ts"])
    frames["returns_quality"]["created_ts"] = pd.to_datetime(frames["returns_quality"]["created_ts"])
    frames["receipts"]["receipt_date"] = pd.to_datetime(frames["receipts"]["receipt_date"])
    _FRAMES = frames
    return frames


def matrix_row(trigger: str) -> dict:
    frame = load_frames()["escalation_matrix"]
    hit = frame[frame["trigger"] == trigger]
    if hit.empty:
        raise KeyError(f"No escalation_matrix row for trigger: {trigger}")
    row = hit.iloc[0]
    return {
        "category": str(row["category"]),
        "trigger": str(row["trigger"]),
        "priority": str(row["priority"]),
        "team": str(row["team"]),
        "channel": str(row["channel"]),
        "sla_minutes": int(row["sla_minutes"]),
        "human_approval_required": _as_bool(row["human_approval_required"]),
        "policy_source": str(row["policy_source"]),
    }


def trigger_for_labels(category: str, priority: str, issue: str) -> str:
    """Map a labelled support case onto one escalation-matrix trigger.

    The matrix can list several triggers for one category. Priority picks the row,
    and a few words in the issue break the remaining ties (warehouse vs stock-out,
    store-wide vs one register). Standard return guidance is the P3 returns row
    the matrix does not list.
    """
    lowered = issue.lower()
    if category == "POS and Payments":
        if priority == "P1" or "all registers" in lowered:
            return "Multiple registers or store-wide payment outage"
        return "One register or one card reader failing"
    if category == "Pricing and Promotions":
        if priority == "P2":
            return "Department or multi-customer pricing mismatch"
        return "Single SKU shelf-vs-register mismatch"
    if category == "Returns and Refunds":
        if priority in {"P1", "P2"}:
            return "No-receipt or high-value refund threshold"
        return "Standard return guidance"
    if category == "Inventory and Replenishment":
        if "academy" in lowered or "warehouse" in lowered:
            return "Warehouse stock depleted for high-demand or academy-order item"
        if priority == "P3":
            return "Routine reorder or cycle count"
        return "High-demand SKU stock-out or false availability"
    if category == "Vendor and Supply Chain":
        return "Repeated or below-90-percent short shipment"
    if category == "Product Quality and Safety":
        if priority == "P1" or re.search(r"injur|recall|unsafe", lowered):
            return "Contamination, injury, recall, or unsafe equipment"
        return "Repeated quality complaints without immediate safety risk"
    if category == "Customer Service":
        return "Routine service recovery"
    if priority == "P1":
        return "Restricted data, prompt injection, or suspicious request"
    return "General inquiry or analytics"


def resolve_sku(text: str, store_id: str | None = None) -> dict | None:
    """Match an explicit code, a catalog name, a price plus noun, a seam defect, then a fuzzy name."""
    products = load_frames()["product_master"]
    by_code = _explicit_sku(text, products)
    if by_code is not None:
        return by_code
    lowered = text.lower()
    by_name = _longest_name_in_text(products, lowered)
    if by_name is not None:
        return by_name
    by_price = _price_and_noun(products, text, lowered)
    if by_price is not None:
        return by_price
    by_seam = _sku_for_seam_football(lowered)
    if by_seam is not None:
        return by_seam
    if store_id is None:
        store_match = _STORE_CODE.search(text)
        store_id = store_match.group(1).upper() if store_match else None
    return _fuzzy_sku(lowered, store_id)


def open_high_priority(hours: int = 24) -> dict:
    cases = _cases_as_of_now()
    start = config.NOW - pd.Timedelta(hours=hours)
    window = cases[
        (cases["created_ts"] >= start)
        & (cases["created_ts"] <= config.NOW)
        & (cases["priority_label"].isin(["P1", "P2"]))
        & (cases["status"].str.lower() != "closed")
    ]
    total = int(len(window))
    facts = [
        (
            f"From {start:%Y-%m-%d %H:%M:%S} IST to {config.NOW:%Y-%m-%d %H:%M:%S} IST, "
            f"support_cases.csv has {total} unresolved P1 or P2 cases. Unresolved means status is not Closed."
        )
    ]
    by_store = []
    if total:
        grouped = (
            window.groupby(["store_id", "priority_label"], dropna=False)
            .size()
            .reset_index(name="n")
            .sort_values(["store_id", "priority_label"])
        )
        for store_id, store_rows in grouped.groupby("store_id"):
            bits = [f"{row.priority_label} {int(row.n)}" for row in store_rows.itertuples()]
            count = int(store_rows["n"].sum())
            facts.append(f"{store_id}: {count} unresolved ({', '.join(bits)}).")
            by_store.append({"store_id": str(store_id), "count": count})
    return {
        "tool": "open_high_priority",
        "files": ["support_cases.csv"],
        "facts": facts,
        "summary": {"total": total, "hours": hours, "by_store": by_store},
    }


def stock_root_cause(store: str | None, sku: str | None) -> dict:
    if not store or not sku:
        return _empty_tool(
            "stock_root_cause",
            "Store ID or SKU is missing, so no inventory figures were calculated.",
        )
    frames = load_frames()
    inventory = frames["inventory"]
    products = frames["product_master"]
    receipts = frames["receipts"]
    vendors = frames["vendor_master"]
    stores = frames["store_master"]
    product = products[products["sku"] == sku]
    product_name = str(product.iloc[0]["name"]) if not product.empty else sku
    vendor_id = str(product.iloc[0]["vendor_id"]) if not product.empty else ""
    high_demand = str(product.iloc[0]["high_demand"]) if not product.empty else ""
    row = inventory[(inventory["store_id"] == store) & (inventory["sku"] == sku)]
    if row.empty:
        return _empty_tool(
            "stock_root_cause",
            f"inventory.csv has no row for {store} {sku}.",
            files=["inventory.csv", "product_master.csv"],
        )
    item = row.iloc[0]
    on_hand = int(item["on_hand"])
    system_qty = int(item["system_qty"])
    reorder_point = int(item["reorder_point"])
    warehouse = inventory[(inventory["sku"] == sku) & (inventory["store_id"].astype(str).str.startswith("WH"))]
    wh_zero = (not warehouse.empty) and bool((warehouse["on_hand"] == 0).all()) and on_hand == 0
    recent = receipts[(receipts["store_id"].isin([store, *warehouse["store_id"].tolist()])) & (receipts["sku"] == sku)]
    recent = recent[recent["receipt_date"] <= config.NOW].sort_values("receipt_date")
    shorts = _short_rows(recent)
    vendor = vendors[vendors["vendor_id"] == vendor_id]
    fill_rate = float(vendor.iloc[0]["fill_rate"]) if not vendor.empty else None
    on_time = float(vendor.iloc[0]["on_time_rate"]) if not vendor.empty else None
    vendor_name = str(vendor.iloc[0]["name"]) if not vendor.empty else vendor_id
    cause = _pick_cause(wh_zero, shorts, fill_rate, on_hand)
    facts = [
        f"Likely root cause: {cause}.",
        (
            f"{store} {sku} {product_name}: on_hand {on_hand}, system_qty {system_qty}, "
            f"reorder_point {reorder_point}, high_demand {high_demand}."
        ),
    ]
    diff = abs(on_hand - system_qty)
    base = max(on_hand, system_qty, 1)
    if diff > config.DISCREPANCY_UNITS or (diff / base) > config.DISCREPANCY_RATIO:
        facts.append(
            f"system_qty and on_hand differ by {diff} units, which is more than 20 percent, so a cycle count is also due."
        )
    for receipt in shorts.tail(2).itertuples():
        ratio = int(receipt.received_qty) / int(receipt.po_qty) if int(receipt.po_qty) else 0
        note = "" if pd.isna(receipt.damage_notes) else str(receipt.damage_notes)
        note_bit = f" Note: {note}." if note and note.lower() != "nan" else ""
        facts.append(
            f"Receipt {receipt.receipt_id} at {receipt.store_id}: received {int(receipt.received_qty)} of "
            f"{int(receipt.po_qty)} on {pd.Timestamp(receipt.receipt_date):%Y-%m-%d} ({ratio:.0%}).{note_bit}"
        )
    if fill_rate is not None:
        facts.append(
            f"Vendor {vendor_id} {vendor_name}: fill_rate {fill_rate:.2f}, on_time_rate {on_time:.2f}."
        )
    for wh in warehouse.itertuples():
        facts.append(f"{wh.store_id} {sku}: on_hand {int(wh.on_hand)}, system_qty {int(wh.system_qty)}.")
    facts.extend(_nearby_fact(stores, inventory, store, sku))
    facts.extend(_case_facts(store, sku))
    claim = "short shipment" in cause
    return {
        "tool": "stock_root_cause",
        "files": [
            "inventory.csv",
            "product_master.csv",
            "receipts.csv",
            "vendor_master.csv",
            "store_master.csv",
            "support_cases.csv",
        ],
        "facts": facts,
        "summary": {
            "likely_cause": cause,
            "vendor_id": vendor_id,
            "vendor_claim": claim,
            "store_id": store,
            "sku": sku,
        },
    }


def short_shipments(vendor: str | None = None, sku: str | None = None) -> dict:
    receipts = load_frames()["receipts"]
    rows = receipts[receipts["receipt_date"] <= config.NOW].copy()
    if vendor:
        rows = rows[rows["vendor_id"] == vendor]
    if sku:
        rows = rows[rows["sku"] == sku]
    shorts = rows[rows["received_qty"] < rows["po_qty"]].sort_values("receipt_date")
    facts = [f"receipts.csv has {int(len(shorts))} short shipments in the current filter."]
    for receipt in shorts.tail(5).itertuples():
        facts.append(
            f"{receipt.receipt_id} {receipt.store_id} {receipt.sku} {receipt.vendor_id}: "
            f"received {int(receipt.received_qty)} of {int(receipt.po_qty)} on {pd.Timestamp(receipt.receipt_date):%Y-%m-%d}."
        )
    below = shorts[shorts["received_qty"] < shorts["po_qty"] * config.SHORT_SHIP_RATIO]
    return {
        "tool": "short_shipments",
        "files": ["receipts.csv"],
        "facts": facts,
        "summary": {
            "count": int(len(shorts)),
            "below_90_percent": int(len(below)),
            "vendor_claim": int(len(below)) > 0,
            "vendor_id": vendor,
            "sku": sku,
        },
    }


def vendor_quality_ranking(days: int = 30) -> dict:
    """Count quality support cases plus quality returns, joined to the product vendor."""
    start = config.NOW - pd.Timedelta(days=days)
    frames = load_frames()
    products = frames["product_master"][["sku", "vendor_id", "name"]]
    vendors = frames["vendor_master"]
    cases = _cases_as_of_now()
    cases = cases[
        (cases["created_ts"] >= start)
        & (cases["created_ts"] <= config.NOW)
        & (cases["category_label"] == "Product Quality and Safety")
    ]
    cases = cases.merge(products, on="sku", how="inner")
    returns = frames["returns_quality"]
    returns = returns[(returns["created_ts"] >= start) & (returns["created_ts"] <= config.NOW)]
    returns = returns[returns["reason"].fillna("").str.contains(QUALITY_REASON)]
    returns = returns.merge(products, on="sku", how="inner")
    case_counts = cases.groupby("vendor_id").size().rename("cases")
    return_counts = returns.groupby("vendor_id").size().rename("returns")
    ranking = (
        pd.concat([case_counts, return_counts], axis=1)
        .fillna(0)
        .astype(int)
        .reset_index()
    )
    ranking["n"] = ranking["cases"] + ranking["returns"]
    ranking = ranking.merge(vendors, on="vendor_id", how="left").sort_values(
        ["n", "vendor_id"], ascending=[False, True]
    )
    if ranking.empty:
        return _empty_tool("vendor_quality_ranking", "No quality complaints fell in the window.", files=[
            "vendor_master.csv",
            "support_cases.csv",
            "returns_quality.csv",
            "product_master.csv",
        ])
    top = ranking.iloc[0]
    facts = [
        (
            f"In the last {days} days ending {config.NOW:%Y-%m-%d %H:%M:%S} IST, "
            f"{top['name']} ({top['vendor_id']}) is linked to the most sports-goods quality complaints "
            f"({int(top['n'])} records: {int(top['cases'])} support cases and {int(top['returns'])} returns). "
            f"Fill rate is {float(top['fill_rate']):.2f} and on-time rate is {float(top['on_time_rate']):.2f}. "
            "This ranks records for review and is not a finding of fault."
        )
    ]
    runners = []
    for row in ranking.iloc[1:3].itertuples():
        runners.append(f"{row.name} ({row.vendor_id}) {int(row.n)}")
    if runners:
        facts.append("Next in the same count: " + "; ".join(runners) + ".")
    return {
        "tool": "vendor_quality_ranking",
        "files": ["vendor_master.csv", "support_cases.csv", "returns_quality.csv", "product_master.csv"],
        "facts": facts,
        "summary": {
            "vendor_id": str(top["vendor_id"]),
            "vendor_name": str(top["name"]),
            "count": int(top["n"]),
            "vendor_claim": False,
        },
    }


def lowest_fill_rate() -> dict:
    """The vendor_master row with the lowest fill rate. Ties break on vendor id."""
    vendors = load_frames()["vendor_master"].sort_values(["fill_rate", "vendor_id"])
    row = vendors.iloc[0]
    vendor_id = str(row["vendor_id"])
    fill = float(row["fill_rate"])
    return {
        "tool": "lowest_fill_rate",
        "files": ["vendor_master.csv"],
        "facts": [
            f"Lowest fill rate in vendor_master.csv is {vendor_id} {row['name']} at {fill:.2f}."
        ],
        "summary": {"vendor_id": vendor_id, "fill_rate": fill, "vendor_claim": False},
    }


def repeated_stockouts() -> dict:
    """SKUs whose on-hand is zero at two or more stores."""
    frames = load_frames()
    inventory = frames["inventory"]
    products = frames["product_master"]
    zero = inventory[inventory["on_hand"] == 0]
    counts = zero.groupby("sku").size()
    repeated = counts[counts >= 2].sort_values(ascending=False)
    facts = []
    for sku, count in repeated.items():
        stores = sorted(zero.loc[zero["sku"] == sku, "store_id"].astype(str).unique())
        name_hit = products[products["sku"] == sku]
        name = str(name_hit.iloc[0]["name"]) if not name_hit.empty else str(sku)
        facts.append(f"{sku} {name} on_hand 0 at {', '.join(stores)} ({int(count)} stores).")
    if not facts:
        facts.append("No SKU is on_hand 0 at two or more stores.")
    return {
        "tool": "repeated_stockouts",
        "files": ["inventory.csv"],
        "facts": facts,
        "summary": {"sku_count": int(len(repeated))},
    }


def quality_trend(sku: str | None = None) -> dict:
    start = config.NOW - pd.Timedelta(days=30)
    frames = load_frames()
    products = frames["product_master"]
    returns = frames["returns_quality"]
    returns = returns[(returns["created_ts"] >= start) & (returns["created_ts"] <= config.NOW)]
    cases = _cases_as_of_now()
    cases = cases[
        (cases["created_ts"] >= start)
        & (cases["created_ts"] <= config.NOW)
        & (cases["category_label"] == "Product Quality and Safety")
    ]
    if sku:
        returns = returns[returns["sku"] == sku]
        cases = cases[cases["sku"] == sku]
        name_hit = products[products["sku"] == sku]
        label = f"{sku} {name_hit.iloc[0]['name']}" if not name_hit.empty else sku
    else:
        label = "all SKUs"
    quality_returns = returns[returns["reason"].fillna("").str.contains(QUALITY_REASON)]
    reason_counts = quality_returns["reason"].value_counts().head(4)
    reason_text = ", ".join(f"{reason} ({int(count)})" for reason, count in reason_counts.items()) or "none"
    stores = sorted(quality_returns["store_id"].dropna().unique().tolist())
    facts = [
        (
            f"In the last 30 days, {label} has {int(len(quality_returns))} quality-related returns "
            f"and {int(len(cases))} product-quality support cases."
        ),
        f"Return reasons: {reason_text}.",
        f"Stores on those quality returns: {', '.join(stores) if stores else 'none'}.",
    ]
    return {
        "tool": "quality_trend",
        "files": ["returns_quality.csv", "support_cases.csv", "product_master.csv"],
        "facts": facts,
        "summary": {"sku": sku, "vendor_claim": False},
    }


def returns_over_threshold(
    sku: str | None = None,
    amount: float | None = None,
    no_receipt: bool | None = None,
) -> dict:
    """List how many returns cross the approval cutoffs. Optional filters narrow the example row."""
    frame = load_frames()["returns_quality"]
    frame = frame[frame["created_ts"] <= config.NOW].copy()
    no_flag = frame["receipt_present"].astype(str).str.lower().eq("no")
    over = (frame["refund_amount_inr"] >= config.REFUND_APPROVAL_INR) | (
        no_flag & (frame["refund_amount_inr"] >= config.NO_RECEIPT_APPROVAL_INR)
    )
    screened = frame[over]
    facts = [
        (
            f"returns_quality.csv has {int(len(screened))} returns at or above the approval cutoffs "
            f"(refund >= {config.REFUND_APPROVAL_INR}, or no receipt and refund >= {config.NO_RECEIPT_APPROVAL_INR})."
        )
    ]
    if amount is not None:
        match = frame[frame["refund_amount_inr"] == amount]
        if no_receipt:
            match = match[no_flag.loc[match.index]]
        if sku:
            sku_match = match[match["sku"] == sku]
            if not sku_match.empty:
                match = sku_match
        if not match.empty:
            row = match.iloc[0]
            receipt = str(row["receipt_present"])
            facts.append(
                f"Matching open row {row['return_id']} is SKU {row['sku']} for INR {int(row['refund_amount_inr'])} "
                f"with receipt_present {receipt} at {row['store_id']}."
            )
        qualifier = "no-receipt " if no_receipt else ""
        facts.append(
            f"The request amount INR {amount:.0f} ({qualifier}return) meets the cutoff for manager review."
        )
    return {
        "tool": "returns_over_threshold",
        "files": ["returns_quality.csv"],
        "facts": facts,
        "summary": {"count": int(len(screened)), "vendor_claim": False},
    }


def _cases_as_of_now() -> pd.DataFrame:
    cases = load_frames()["support_cases"]
    return cases[cases["created_ts"] <= config.NOW].copy()


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"yes", "true", "1"}


def _explicit_sku(text: str, products: pd.DataFrame) -> dict | None:
    match = _SKU_CODE.search(text)
    if not match:
        return None
    token = match.group(1).upper()
    hit = products[products["sku"].str.upper() == token]
    if hit.empty:
        return None
    return _product_dict(hit.iloc[0])


def _fuzzy_sku(lowered: str, store_id: str | None) -> dict | None:
    """Fallback only. Score is the share of catalog-name tokens found in the query."""
    vocab, entries = _product_name_index()
    query_tokens = {_singular(token, vocab) for token in re.findall(r"[a-z0-9]+", lowered)}
    if not query_tokens:
        return None
    best_score = 0.0
    tied: list[tuple[float, int, object]] = []
    for tokens, row in entries:
        if not tokens:
            continue
        matched = [token for token in tokens if token in query_tokens]
        score = len(matched) / len(tokens)
        non_generic = sum(1 for token in matched if token not in _GENERIC_TOKENS and not token.isdigit())
        if score < 0.6 or non_generic < 2:
            continue
        if score > best_score + 1e-9:
            best_score = score
            tied = [(score, non_generic, row)]
        elif abs(score - best_score) <= 1e-9:
            tied.append((score, non_generic, row))
    if not tied:
        return None
    frames = load_frames()
    winner = min(tied, key=lambda item: _fuzzy_sort_key(item[2], store_id, frames))
    return _product_dict(winner[2])


def _fuzzy_sort_key(row, store_id: str | None, frames: dict[str, pd.DataFrame]) -> tuple:
    """Lower is better: a row at the named store, then high demand, then more cases, then sku."""
    sku = str(row.sku)
    at_store = 0
    case_count = 0
    if store_id:
        inventory = frames["inventory"]
        stocked = inventory[(inventory["store_id"] == store_id) & (inventory["sku"] == sku)]
        at_store = 0 if not stocked.empty else 1
        cases = frames["support_cases"]
        case_count = int(((cases["store_id"] == store_id) & (cases["sku"] == sku)).sum())
    high_demand = 0 if str(row.high_demand).strip().lower() == "yes" else 1
    return (at_store, high_demand, -case_count, sku)


def _product_name_index() -> tuple[set[str], list[tuple[list[str], object]]]:
    global _NAME_INDEX
    if _NAME_INDEX is not None:
        return _NAME_INDEX
    products = load_frames()["product_master"]
    vocab: set[str] = set()
    entries: list[tuple[list[str], object]] = []
    for row in products.itertuples(index=False):
        tokens = re.findall(r"[a-z0-9]+", str(row.name).lower())
        vocab.update(tokens)
        entries.append((tokens, row))
    _NAME_INDEX = (vocab, entries)
    return _NAME_INDEX


def _singular(token: str, vocab: set[str]) -> str:
    if token.endswith("s") and token[:-1] in vocab:
        return token[:-1]
    return token


def _longest_name_in_text(products: pd.DataFrame, lowered: str) -> dict | None:
    hits: list[tuple[int, pd.Series]] = []
    for row in products.itertuples(index=False):
        for base in _name_bases(str(row.name)):
            if len(base) >= 8 and base in lowered:
                hits.append((len(base), row))
    if not hits:
        return None
    _length, best = max(hits, key=lambda item: item[0])
    return _product_dict(best)


def _name_bases(name: str) -> list[str]:
    raw = name.lower().strip()
    stripped = re.sub(r"\s+size\s+\d+$", "", raw)
    stripped = re.sub(r"\s+\d+$", "", stripped).strip()
    bases = [raw]
    if stripped and stripped != raw:
        bases.append(stripped)
    return bases


def _price_and_noun(products: pd.DataFrame, text: str, lowered: str) -> dict | None:
    match = re.search(r"\bINR\s*([0-9][0-9,]*)", text, flags=re.IGNORECASE)
    if not match:
        return None
    amount = float(match.group(1).replace(",", ""))
    for noun in ("treadmill", "exercise bike", "cricket bat", "football"):
        if noun not in lowered:
            continue
        hits = products[
            products["name"].str.lower().str.contains(noun, regex=False)
            & (products["list_price"] == amount)
        ]
        if len(hits) == 1:
            return _product_dict(hits.iloc[0])
    return None


def _sku_for_seam_football(lowered: str) -> dict | None:
    if "seam" not in lowered or "football" not in lowered:
        return None
    frames = load_frames()
    returns = frames["returns_quality"]
    products = frames["product_master"]
    seam = returns[returns["reason"].fillna("").str.contains("seam", case=False)]
    merged = seam.merge(products, on="sku", how="left")
    merged = merged[merged["name"].fillna("").str.contains("football", case=False)]
    if merged.empty:
        return None
    top_sku = merged["sku"].value_counts().index[0]
    row = products[products["sku"] == top_sku].iloc[0]
    return _product_dict(row)


def _product_dict(row) -> dict:
    return {
        "sku": str(row.sku),
        "name": str(row.name),
        "vendor_id": str(row.vendor_id),
        "list_price": float(row.list_price),
        "high_demand": str(row.high_demand),
    }


def _short_rows(receipts: pd.DataFrame) -> pd.DataFrame:
    if receipts.empty:
        return receipts
    return receipts[receipts["received_qty"] < receipts["po_qty"]]


def _pick_cause(wh_zero: bool, shorts: pd.DataFrame, fill_rate: float | None, on_hand: int) -> str:
    if wh_zero:
        return "warehouse stock depleted"
    below_90 = False
    if not shorts.empty:
        below_90 = bool((shorts["received_qty"] < shorts["po_qty"] * config.SHORT_SHIP_RATIO).any())
    consecutive = len(shorts) >= 2
    low_fill = fill_rate is not None and fill_rate < config.FILL_RATE_WARNING
    if consecutive and low_fill:
        return "likely linked to repeated short shipment and low vendor fill rate"
    if below_90 and low_fill:
        return "likely linked to short shipment and low vendor fill rate"
    if below_90 or consecutive:
        return "likely linked to short shipment"
    if low_fill and on_hand == 0:
        return "likely linked to low vendor fill rate"
    if on_hand == 0:
        return "on-hand is zero and needs a receipt review"
    return "requires review; the files do not show one cause"


def _nearby_fact(stores: pd.DataFrame, inventory: pd.DataFrame, store: str, sku: str) -> list[str]:
    store_row = stores[stores["store_id"] == store]
    if store_row.empty or pd.isna(store_row.iloc[0]["nearby_store_id"]):
        return []
    nearby = str(store_row.iloc[0]["nearby_store_id"])
    row = inventory[(inventory["store_id"] == nearby) & (inventory["sku"] == sku)]
    if row.empty:
        return []
    return [f"Nearby store {nearby} has {int(row.iloc[0]['on_hand'])} on hand for {sku}."]


def _case_facts(store: str, sku: str) -> list[str]:
    cases = _cases_as_of_now()
    related = cases[(cases["store_id"] == store) & (cases["sku"] == sku)]
    if related.empty:
        return [f"support_cases.csv has no case at {store} for {sku} on or before the anchor time."]
    latest = related.sort_values("created_ts").iloc[-1]
    hint = "" if pd.isna(latest["root_cause_hint"]) else str(latest["root_cause_hint"])
    hint_bit = f" Latest hint on {latest['case_id']}: {hint}." if hint else ""
    return [f"support_cases.csv has {int(len(related))} related cases at {store} for {sku}.{hint_bit}"]


def _empty_tool(tool: str, fact: str, files: list[str] | None = None) -> dict:
    return {
        "tool": tool,
        "files": files or [],
        "facts": [fact],
        "summary": {"vendor_claim": False, "likely_cause": "insufficient detail"},
    }
