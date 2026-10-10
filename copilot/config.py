"""Paths, the event clock, and the numeric cutoffs copied from the knowledge base."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
USE_CASE_DIR = ROOT / "Use Case 3"
KB_DIR = USE_CASE_DIR / "knowledge_base"
DATA_DIR = USE_CASE_DIR / "data"
EVAL_DIR = USE_CASE_DIR / "evaluation"
PREDICTIONS_PATH = EVAL_DIR / "predictions.csv"
LOG_PATH = ROOT / "logs" / "trace.jsonl"
OUTBOX_DIR = ROOT / "outbox"

# Business "now" for last-24-hours and last-30-days questions.
# The CSV clocks have no timezone; treat them as this same IST clock.
NOW = datetime(2026, 10, 10, 12, 0, 0)

# Stricter than the SOP sentence "below 0.60". This build escalates under 0.65.
CONF_ESCALATE = 0.65

# 02_pos_pricing_returns_policy.md#returns-and-refunds
REFUND_APPROVAL_INR = 5000
NO_RECEIPT_APPROVAL_INR = 1000

# 04_vendor_quality_policy.md#short-shipments and #vendor-performance
SHORT_SHIP_RATIO = 0.90
FILL_RATE_WARNING = 0.80
ON_TIME_WARNING = 0.85

# 03_inventory_replenishment_policy.md#inventory-discrepancy
DISCREPANCY_UNITS = 10
DISCREPANCY_RATIO = 0.20

BM25_EXTRA_HITS = 2
MAX_CHUNKS = 6

LLM_BACKEND = os.getenv("LLM_BACKEND", "RULES_ONLY").strip() or "RULES_ONLY"
