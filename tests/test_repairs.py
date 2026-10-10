"""Checks for the cascade repairs. Phrasings here are not suite prompts."""

from copilot.agents.composer import build, cite_line
from copilot.agents.data_agent import lookup
from copilot.agents.retrieval import _is_weak
from copilot.agents.triage import classify_rules
from copilot.data import resolve_sku
from copilot.kb import chunk_ids, load_chunks
from copilot.lexicon import apply_lexicon


def test_explicit_and_fuzzy_sku_resolution():
    coded = resolve_sku("Count the shelf for SKU1001 before the shift ends.")
    assert coded is not None and coded["sku"] == "SKU1001"
    bat = resolve_sku("The english willow bats up front at ST002 are gone.")
    assert bat is not None and bat["sku"] == "SKU1001"
    balls = resolve_sku("We are short of tennis balls at ST005 this morning.")
    assert balls is not None and balls["sku"] == "SKU7001"
    assert resolve_sku("Please restock cricket bats") is None
    assert resolve_sku("The footballs arrived late") is None


def test_tool_facts_are_copied_verbatim_into_the_answer():
    text = "English willow bats are out of stock at ST002. Trace the shortage from the last receipts."
    findings = lookup(text, {"intent": "stock_root_cause", "store_id": None, "sku": None}, {})
    assert findings.facts
    assert "inventory.csv" in findings.files
    state = {
        "masked_text": text,
        "safety": {},
        "triage": {
            "category": "Inventory and Replenishment",
            "priority": "P2",
            "confidence": 0.93,
            "reasoning": "A high-demand item is unavailable.",
            "team": "Store Manager + Inventory Lead",
            "policy_source": "03_inventory_replenishment_policy.md#stock-outs-and-replenishment",
            "human_approval_required": False,
            "intent": "stock_root_cause",
            "store_id": "ST002",
            "sku": "SKU1001",
        },
        "retrieval": {"chunks": [], "weak": False},
        "data_findings": findings.model_dump(),
        "escalation": {"required": False, "team": None, "reason": None},
    }
    response = build(state)
    for fact in findings.facts:
        assert fact in response.answer
    assert response.data_used == findings.files


def test_every_chunk_has_a_cite_line():
    ids = chunk_ids()
    assert ids
    for chunk_id in ids:
        line = cite_line(chunk_id, {})
        assert line
        assert line.strip()
        heading = next(chunk.heading for chunk in load_chunks() if chunk.id == chunk_id)
        assert not line.startswith(heading + "\n")


def test_customer_recovery_and_recall_use_the_written_lines():
    recovery = cite_line("02_pos_pricing_returns_policy.md#customer-recovery", {})
    recall = cite_line("04_vendor_quality_policy.md#recall-and-safety", {})
    assert recovery.startswith("For customer inconvenience")
    assert recall.startswith("Any recall or suspected unsafe product")


def test_negative_rerank_is_weak_only_out_of_scope_or_off_section():
    policy = "03_inventory_replenishment_policy.md#stock-outs-and-replenishment"
    ranked = [policy, "04_vendor_quality_policy.md#short-shipments", "01_retail_operations_sop.md#analytics-rule"]
    assert _is_weak(-2.5, "Inventory and Replenishment", policy, ranked) is False
    assert _is_weak(-2.5, "Other or Security", policy, ranked) is True
    assert _is_weak(-2.5, "Inventory and Replenishment", "04_vendor_quality_policy.md#recall-and-safety", ranked) is True
    assert _is_weak(0.4, "Other or Security", policy, ranked) is False


def test_glossary_ranking_is_quality_and_bad_fill_rate_stays_vendor():
    ranking = classify_rules("Kaunsa supplier ne pichhle mahine sabse zyada kharab maal bheja?", {})
    assert ranking.category == "Product Quality and Safety"
    assert ranking.priority == "P2"
    assert ranking.intent == "vendor_quality_ranking"
    shipment = classify_rules("Vendor fill rate kharab hai, received only half the order.", {})
    assert shipment.category == "Vendor and Supply Chain"
    assert shipment.trigger == "Repeated or below-90-percent short shipment"


def test_godown_is_the_warehouse_stock_row():
    decision = classify_rules("Goods are out of stock in the godown and the shop floor is empty.", {})
    assert decision.trigger == "Warehouse stock depleted for high-demand or academy-order item"


def test_lexicon_does_not_rewrite_the_callers_string():
    original = "maal kharab"
    assert apply_lexicon(original) == "goods bad"
    assert original == "maal kharab"
