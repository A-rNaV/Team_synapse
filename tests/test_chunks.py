import csv

from copilot.config import EVAL_DIR
from copilot.kb import chunk_ids, slug


def test_public_expected_sources_are_chunk_ids():
    known = set(chunk_ids())
    with (EVAL_DIR / "public_test_cases.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            for source in row["expected_sources"].split(";"):
                assert source in known, source


def test_heading_slugs_match_the_citation_format():
    assert slug("POS Card Reader Runbook") == "pos-card-reader-runbook"
    assert slug("PII and Payment Data Masking") == "pii-and-payment-data-masking"
    assert slug("Stock-Outs and Replenishment") == "stock-outs-and-replenishment"
    assert slug("Root-Cause Hints") == "root-cause-hints"
    assert slug("Human-in-the-Loop") == "human-in-the-loop"
