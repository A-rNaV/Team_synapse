"""Pick one pandas tool from the triage intent. The tool, not the model, supplies numbers."""

from __future__ import annotations

import re
import time

from copilot import data, trace
from copilot.schemas import DataFindings


def lookup(masked_text: str, triage: dict, safety: dict) -> DataFindings:
    if safety.get("refusal"):
        return DataFindings(tool="", files=[], facts=[], summary={})
    intent = triage.get("intent") or ""
    if intent == "open_high_priority":
        payload = data.open_high_priority(_hours(masked_text))
    elif intent == "stock_root_cause":
        store, sku = _store_and_sku(masked_text, triage)
        payload = data.stock_root_cause(store, sku)
    elif intent == "short_shipments":
        payload = data.short_shipments(_vendor(masked_text), triage.get("sku"))
    elif intent == "vendor_quality_ranking":
        payload = data.vendor_quality_ranking(_days(masked_text))
    elif intent == "lowest_fill_rate":
        payload = data.lowest_fill_rate()
    elif intent == "repeated_stockouts":
        payload = data.repeated_stockouts()
    elif intent == "quality_trend":
        payload = data.quality_trend(triage.get("sku"))
    elif intent == "returns_over_threshold":
        payload = data.returns_over_threshold(
            sku=triage.get("sku"),
            amount=triage.get("refund_amount"),
            no_receipt=bool(triage.get("no_receipt")),
        )
    else:
        payload = {"tool": "", "files": [], "facts": [], "summary": {}}
    return DataFindings.model_validate(payload)


def data_node(state: dict) -> dict:
    started = time.perf_counter()
    findings = lookup(
        state.get("masked_text") or "",
        state.get("triage") or {},
        state.get("safety") or {},
    )
    update = {"data_findings": findings.model_dump()}
    update["trace"] = [
        trace.record(
            request_id=state.get("request_id", ""),
            agent="data",
            mode="rule",
            started=started,
            input_summary={"intent": (state.get("triage") or {}).get("intent", "")},
            output_summary={"tool": findings.tool, "files": findings.files, "facts": findings.facts},
        )
    ]
    return update


def _hours(text: str) -> int:
    match = re.search(r"last\s+(\d+)\s+hours", text, flags=re.IGNORECASE)
    return int(match.group(1)) if match else 24


def _days(text: str) -> int:
    match = re.search(r"last\s+(\d+)\s+days", text, flags=re.IGNORECASE)
    return int(match.group(1)) if match else 30


def _vendor(text: str) -> str | None:
    match = re.search(r"\bV\d{3}\b", text, flags=re.IGNORECASE)
    return match.group(0).upper() if match else None


def _store_and_sku(text: str, triage: dict) -> tuple[str | None, str | None]:
    """Re-read the message when triage left the store or the SKU blank."""
    store = triage.get("store_id") or _store_id(text)
    sku = triage.get("sku")
    if store and sku:
        return store, sku
    product = data.resolve_sku(text, store_id=store)
    if not sku and product is not None:
        sku = product["sku"]
    if not store:
        store = _store_id(text)
    return store, sku


def _store_id(text: str) -> str | None:
    match = re.search(r"\b((?:ST|WH)\d{3})\b", text, flags=re.IGNORECASE)
    return match.group(1).upper() if match else None
