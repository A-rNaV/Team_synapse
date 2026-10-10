"""Append one JSON line per agent step. Strings are masked before the write."""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone

from copilot.config import LOG_PATH

_WRITE_LOCK = threading.Lock()


def record(
    request_id: str,
    agent: str,
    mode: str,
    started: float,
    input_summary,
    output_summary,
) -> dict:
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "request_id": request_id,
        "agent": agent,
        "mode": mode,
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        "input": _scrub(input_summary),
        "output": _scrub(output_summary),
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=True) + "\n"
    with _WRITE_LOCK:
        with LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(line)
    return entry


def _scrub(value):
    # Imported here so safety.py can import this module without a cycle.
    from copilot.agents.safety import mask_text

    if isinstance(value, str):
        return mask_text(value).text
    if isinstance(value, dict):
        return {key: _scrub(item) for key, item in value.items() if key != "raw_text"}
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, float):
        return round(value, 4)
    return value
