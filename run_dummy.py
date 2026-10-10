"""Run Use Case 3/evaluation/dummy_cases.csv and write a results table.

This set is separate from the scored suites. Category and priority are checked
against the expected columns. The answer text is kept for reading.
"""

from __future__ import annotations

import os

import pandas as pd

os.environ.setdefault("LLM_BACKEND", "RULES_ONLY")
os.environ.setdefault("TRIAGE_PATH", "cascade")

from copilot.config import EVAL_DIR
from copilot.graph import run_turn
from copilot.warmup import warmup

CASES_PATH = EVAL_DIR / "dummy_cases.csv"
OUT_PATH = EVAL_DIR / "results" / "dummy_run.csv"


def main() -> None:
    warmup()
    cases = pd.read_csv(CASES_PATH)
    rows = []
    for case in cases.itertuples(index=False):
        response, _steps = run_turn(str(case.prompt), persona=str(case.persona), request_id=str(case.test_id))
        expected_source = str(case.expected_sources)
        cited = list(response.citations)
        route_ok = response.category == case.expected_category and response.priority == case.expected_priority
        rows.append(
            {
                "test_id": case.test_id,
                "expected_category": case.expected_category,
                "got_category": response.category,
                "expected_priority": case.expected_priority,
                "got_priority": response.priority,
                "route_ok": route_ok,
                "source_cited": expected_source in cited,
                "confidence": response.confidence,
                "escalated": response.escalation.required,
                "escalation_team": response.escalation.team or "",
                "pii_masked": response.pii_masked,
                "safety_refusal": response.safety_refusal,
                "citations": ";".join(cited),
                "data_used": ";".join(response.data_used),
                "answer": response.answer,
            }
        )
        mark = "ok" if route_ok else "MISS"
        print(f"{case.test_id} {mark} {response.category} {response.priority} conf={response.confidence:.2f}")
    frame = pd.DataFrame(rows)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT_PATH, index=False)
    passed = int(frame["route_ok"].sum())
    print(f"\n{passed}/{len(frame)} route checks passed")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
