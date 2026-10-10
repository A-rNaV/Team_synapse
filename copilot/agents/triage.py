"""Keyword rules pick one escalation_matrix row. The row supplies category, priority, team, and SLA.

When LLM_BACKEND is not RULES_ONLY, a model proposal is ensembled with those rules.
Priority, team, SLA, and approval still come from the matrix row in code.
"""

from __future__ import annotations

import os
import re
import time
import urllib.error

from pydantic import ValidationError

from copilot import config, trace
from copilot.agents.llm_triage import propose
from copilot.data import QUALITY_REASON, load_frames, matrix_row, resolve_sku
from copilot.lexicon import apply_lexicon
from copilot.llm import LLMUnavailable
from copilot.schemas import LLMTriage, Triage

INJURY_TRIGGER = "Contamination, injury, recall, or unsafe equipment"
STANDARD_RETURN = "Standard return guidance"
STOREWIDE_OUTAGE = "Multiple registers or store-wide payment outage"
ONE_REGISTER = "One register or one card reader failing"

STORE_RE = re.compile(r"\b((?:ST|WH)\d{3})\b", re.IGNORECASE)
INR_RE = re.compile(r"\bINR\s*([0-9][0-9,]*)", re.IGNORECASE)
_QUALITY_CUE: re.Pattern | None = None
# The store-wide P1 row needs the note to say the outage covers the store, not one payment error.
_STOREWIDE_SCOPE_RE = re.compile(
    r"\b(?:all|every|each)\s+(?:the\s+|of\s+the\s+)?(?:registers?|regs?|counters?|tills?|pos|terminals?|checkouts?|card\s+readers?)\b"
    r"|\b(?:entire|whole)\s+(?:the\s+)?(?:store|shop|pos)\b"
    r"|\bstore[- ]?wide\b",
    re.IGNORECASE,
)
# Words that tie an analytics request to the case, stock, or vendor data the tools can read.
_ANALYTICS_CUE_RE = re.compile(
    r"\b(?:how\s+many|count|number\s+of|list(?:ed)?|grouped|summar(?:y|ise|ize)|report|trends?|rank(?:ing)?"
    r"|lowest|highest|worst|open|unresolved|pending|urgent|escalated|tickets?|cases?|incidents?|complaints?"
    r"|p[1-4]|fill\s+rate|short\s+shipments?|stock|vendors?|suppliers?|last\s+\d+\s+(?:hours?|hrs|days))\b",
    re.IGNORECASE,
)

# Checked in this order. The first hit wins.
_CHECKS = []


def classify(text: str, safety: dict) -> Triage:
    path = os.getenv("TRIAGE_PATH", "cascade").strip().lower()
    if path in {"always", "deepseek", "deepseek_always"}:
        return _classify_always(text, safety)
    return _classify_cascade(text, safety)


def _classify_always(text: str, safety: dict) -> Triage:
    """Current ensemble: call DeepSeek on every case the rules do not already settle."""
    rules = _annotate(classify_rules(text, safety))
    if safety.get("refusal"):
        return rules.model_copy(update={"decision_source": "safety"})
    if rules.trigger == INJURY_TRIGGER:
        return rules.model_copy(update={"decision_source": "hard_rule"})
    if _skip_model(rules, safety):
        return rules.model_copy(update={"decision_source": "rules_fallback"})
    try:
        proposal = propose(text)
    except (LLMUnavailable, ValidationError, ValueError, urllib.error.URLError, TimeoutError, OSError):
        return rules.model_copy(update={"decision_mode": "rule_fallback", "decision_source": "rules_fallback"})
    chosen = combine(rules, proposal)
    return chosen.model_copy(update={"decision_source": "llm", "llm_called": True})


def _classify_cascade(text: str, safety: dict) -> Triage:
    """Safety, then hard rules, then kNN category, then a confident rule, then DeepSeek."""
    rules = _annotate(classify_rules(text, safety))
    if safety.get("refusal"):
        return _tag(rules, "safety")
    locked = _layer2(text, safety, rules)
    if locked is not None:
        return locked
    hit = _knn_hit(text)
    neighbours = _neighbour_payload(hit)
    if _category_accepts(hit):
        chosen = _row_for_knn_category(hit, rules, text)
        if chosen is not None:
            return chosen
    if _rule_stands(rules, hit):
        tagged = _tag(rules, "rule", neighbours=neighbours)
        return tagged.model_copy(update={"knn_confidence": None if hit is None else hit.confidence})
    if _skip_model(rules, safety):
        return _tag(rules, "rules_fallback", neighbours=neighbours)
    allowed = _allowed_rows(hit.category) if _category_accepts(hit) else None
    try:
        if allowed:
            proposal = propose(text, neighbours=neighbours, allowed_rows=allowed)
            if proposal.matrix_row_id.value not in set(allowed):
                raise ValueError("matrix row is outside the kNN category")
            if proposal.category != hit.category:
                # The model rejects the kNN category, so that category is not confirmed.
                proposal = propose(text, neighbours=neighbours)
        else:
            proposal = propose(text, neighbours=neighbours)
    except (LLMUnavailable, ValidationError, ValueError, urllib.error.URLError, TimeoutError, OSError):
        return _unavailable(hit, rules)
    return _guard_hard_rules(_ensemble(hit, rules, proposal, text), text, safety)


def classify_rules(text: str, safety: dict) -> Triage:
    entities = _entities(text)
    glossed = apply_lexicon(text)
    for check in _CHECKS:
        decision = check(glossed, safety, entities)
        if decision is not None:
            return decision
    return _fallback(entities)


def triage_node(state: dict) -> dict:
    started = time.perf_counter()
    safety = state.get("safety") or {}
    decision = classify(state.get("masked_text") or "", safety)
    update = {"triage": decision.model_dump()}
    update["trace"] = [
        trace.record(
            request_id=state.get("request_id", ""),
            agent="triage",
            mode=decision.decision_mode,
            started=started,
            input_summary=state.get("masked_text") or "",
            output_summary={
                "category": decision.category,
                "priority": decision.priority,
                "confidence": decision.confidence,
                "trigger": decision.trigger,
                "intent": decision.intent,
                "reasoning": decision.reasoning,
                "decision_mode": decision.decision_mode,
                "agreement": decision.decision_mode == "ensemble" and not decision.disagreement,
                "rules_category": decision.rules_category,
                "rules_priority": decision.rules_priority,
                "rules_trigger": decision.rules_trigger,
                "llm_category": decision.llm_category,
                "llm_trigger": decision.llm_trigger,
                "llm_confidence": decision.llm_confidence,
                "decision_source": decision.decision_source,
                "knn_confidence": decision.knn_confidence,
                "neighbours": decision.neighbours,
                "llm_called": decision.llm_called,
            },
        )
    ]
    return update


def _layer2(text: str, safety: dict, rules: Triage) -> Triage | None:
    """P1 safety and analytics questions stay with the rules. The model cannot override them."""
    text = apply_lexicon(text)
    entities = _entities(text)
    forced = _check_injury(text, safety, entities) or _check_storewide_pos(text, safety, entities)
    if forced is not None:
        return _tag(forced, "hard_rule")
    fill = _fill_rate_report(text, entities)
    if fill is not None:
        return _tag(fill, "hard_rule")
    multi = _multi_store_stock(text, entities)
    if multi is not None:
        return _tag(multi, "hard_rule")
    if rules.confidence >= config.CONF_ESCALATE and rules.intent in {
        "open_high_priority",
        "vendor_quality_ranking",
        "quality_trend",
        "short_shipments",
        "stock_root_cause",
    }:
        return _tag(rules, "hard_rule")
    if rules.confidence >= config.CONF_ESCALATE and re.search(
        r"how many|last\s+\d+\s+hours|grouped by store|unresolved|open cases|\breport\b|\btrends?\b",
        text,
        re.IGNORECASE,
    ):
        return _tag(rules, "hard_rule")
    return None


def _fill_rate_report(text: str, entities: dict) -> Triage | None:
    if not re.search(r"fill rate", text, re.IGNORECASE):
        return None
    if re.search(r"short shipment|received only", text, re.IGNORECASE):
        return None
    if not re.search(r"lowest|worst|which vendor|vendor master", text, re.IGNORECASE):
        return None
    return _from_matrix(
        "General inquiry or analytics",
        "This asks for the lowest vendor fill rate, so the analytics row owns the answer.",
        entities,
        intent="lowest_fill_rate",
        confidence=0.93,
    )


def _multi_store_stock(text: str, entities: dict) -> Triage | None:
    if not re.search(r"two or more|multiple stores|more than one store", text, re.IGNORECASE):
        return None
    if not re.search(r"out of stock|stock-out|stockout|not available", text, re.IGNORECASE):
        return None
    return _from_matrix(
        "High-demand SKU stock-out or false availability",
        "This asks which high-demand items are out of stock in more than one store.",
        entities,
        intent="repeated_stockouts",
        confidence=0.93,
    )


def _tag(decision: Triage, source: str, decision_mode: str | None = None, neighbours: list | None = None) -> Triage:
    update = {
        "decision_source": source,
        "decision_mode": decision_mode or source,
        "llm_called": False,
    }
    if neighbours is not None:
        update["neighbours"] = neighbours
    return decision.model_copy(update=update)


def _knn_hit(text: str):
    try:
        from copilot.knn import lookup

        return lookup(text)
    except Exception:
        return None


def _knn_thresholds() -> tuple[float, float]:
    try:
        from copilot.knn import thresholds

        return thresholds()
    except Exception:
        return 0.75, 0.85


def _category_accepts(hit) -> bool:
    if hit is None:
        return False
    conf_threshold, sim_threshold = _knn_thresholds()
    return hit.confidence >= conf_threshold and hit.top1 >= sim_threshold


def _is_fallback(rules: Triage) -> bool:
    return rules.trigger == "General inquiry or analytics" and rules.confidence < 0.5


def _rule_stands(rules: Triage, hit) -> bool:
    """A specific high-confidence rule is enough when kNN does not name another category."""
    if _is_fallback(rules) or rules.confidence < 0.85:
        return False
    contradicted = (
        hit is not None
        and hit.confidence >= 0.60
        and hit.top1 >= 0.75
        and hit.category != rules.category
    )
    return not contradicted


_SINGLE_ROW = {
    "Customer Service": "Routine service recovery",
    "Vendor and Supply Chain": "Repeated or below-90-percent short shipment",
}


def _row_for_knn_category(hit, rules: Triage, text: str) -> Triage | None:
    """kNN fixes the category. The matrix row comes from the single row, the rules, or None (ask DeepSeek)."""
    entities = _merge_rule_entities(rules)
    category = hit.category
    if rules.category == category and not _is_fallback(rules):
        intent = rules.intent or _intent_for(category, "triage", entities, text)
        return _knn_decision(hit, rules, rules.trigger, intent, entities)
    if category in _SINGLE_ROW:
        trigger = _SINGLE_ROW[category]
        intent = _intent_for(category, "triage", entities, text)
        return _knn_decision(hit, rules, trigger, intent, entities)
    return None


def _knn_decision(hit, rules: Triage, trigger: str, intent: str, entities: dict) -> Triage:
    if rules.category == hit.category and not _is_fallback(rules):
        confidence = float(rules.confidence)
    else:
        confidence = float(hit.confidence)
    decision = _from_trigger(
        trigger,
        f"Nearest labelled cases are {hit.category}. The matrix row is {trigger}.",
        entities,
        intent=intent,
        confidence=confidence,
    )
    return decision.model_copy(
        update={
            "decision_source": "knn",
            "decision_mode": "knn",
            "knn_confidence": hit.confidence,
            "neighbours": _neighbour_payload(hit),
            "llm_called": False,
            "rules_trigger": rules.trigger,
            "rules_category": rules.category,
            "rules_priority": rules.priority,
            "disagreement": False,
        }
    )


def _allowed_rows(category: str) -> list[str]:
    frame = load_frames()["escalation_matrix"]
    rows = [str(item) for item in frame.loc[frame["category"] == category, "trigger"].tolist()]
    if category == "Returns and Refunds":
        rows.append(STANDARD_RETURN)
    return rows


def _unavailable(hit, rules: Triage) -> Triage:
    """No validated DeepSeek reply. Keep the kNN-category row when we have one, else the rules row."""
    draft = None
    if _category_accepts(hit):
        draft = _row_for_knn_category(hit, rules, "")
    if draft is None:
        draft = rules.model_copy(
            update={
                "neighbours": _neighbour_payload(hit),
                "knn_confidence": None if hit is None else hit.confidence,
            }
        )
    return draft.model_copy(
        update={
            "decision_source": "llm_unavailable",
            "decision_mode": "llm_unavailable",
            "confidence": min(float(draft.confidence), 0.5),
            "disagreement": True,
            "llm_called": False,
        }
    )


def _ensemble(hit, rules: Triage, proposal: LLMTriage, text: str) -> Triage:
    row_id = proposal.matrix_row_id.value
    if row_id == STOREWIDE_OUTAGE and not _has_storewide_scope(text):
        row_id = ONE_REGISTER
    row_category = _row_category(row_id)
    entities = _merge_entities(rules, proposal)
    neighbours = _neighbour_payload(hit)
    knn_conf = 0.0 if hit is None else float(hit.confidence)
    agreed = hit is not None and hit.category == row_category
    if agreed:
        confidence = max(float(proposal.confidence), knn_conf)
    else:
        confidence = float(proposal.confidence) * 0.9
    if row_category == "Other or Security" and not _grounded_analytics(proposal, text):
        # A neighbour in this catch-all category is not evidence the note is in scope.
        confidence = min(confidence, 0.5)
    intent = _intent_for(row_category, proposal.intent, entities, text)
    if not intent and rules.category == row_category:
        intent = rules.intent
    base = _from_trigger(
        row_id,
        proposal.reasoning or rules.reasoning,
        entities,
        intent=intent,
        confidence=confidence,
    )
    if confidence < config.CONF_ESCALATE:
        disagreement = True
    else:
        disagreement = False
    return base.model_copy(
        update={
            "confidence": min(max(confidence, 0.0), 1.0),
            "decision_source": "llm",
            "decision_mode": "llm",
            "llm_called": True,
            "llm_trigger": row_id,
            "llm_category": row_category,
            "llm_confidence": proposal.confidence,
            "missing_fields": list(proposal.missing_fields),
            "neighbours": neighbours,
            "knn_confidence": None if hit is None else hit.confidence,
            "disagreement": disagreement,
            "rules_trigger": rules.trigger,
            "rules_category": rules.category,
            "rules_priority": rules.priority,
            "store_id": entities["store_id"],
            "sku": entities["sku"],
            "product_name": entities["product_name"],
            "register_scope": entities["register_scope"],
            "refund_amount": entities["refund_amount"],
            "no_receipt": entities["no_receipt"],
        }
    )


def _has_storewide_scope(text: str) -> bool:
    return _STOREWIDE_SCOPE_RE.search(apply_lexicon(text)) is not None


def _grounded_analytics(proposal: LLMTriage, text: str) -> bool:
    """An analytics intent counts only when the text asks about operational data."""
    return proposal.intent == "analytics" and _ANALYTICS_CUE_RE.search(apply_lexicon(text)) is not None


def _guard_hard_rules(decision: Triage, text: str, safety: dict) -> Triage:
    """A fired P1 rule replaces whatever the model or the neighbours chose."""
    locked = _layer2(text, safety, _annotate(classify_rules(text, safety)))
    if locked is None:
        return decision
    if locked.decision_source == "hard_rule" and (
        locked.trigger in {INJURY_TRIGGER, "Multiple registers or store-wide payment outage"}
        or locked.intent
    ):
        if decision.trigger != locked.trigger or decision.priority != locked.priority:
            return locked.model_copy(update={"neighbours": decision.neighbours, "llm_called": decision.llm_called})
    return decision


def _neighbour_payload(hit) -> list[dict]:
    if hit is None:
        return []
    return list(hit.neighbours)


def _merge_rule_entities(rules: Triage) -> dict:
    return {
        "store_id": rules.store_id,
        "sku": rules.sku,
        "product_name": rules.product_name,
        "register_scope": rules.register_scope,
        "refund_amount": rules.refund_amount,
        "no_receipt": rules.no_receipt,
    }


def _annotate(rules: Triage) -> Triage:
    return rules.model_copy(
        update={
            "rules_trigger": rules.trigger,
            "rules_category": rules.category,
            "rules_priority": rules.priority,
            "decision_mode": "rule",
            "disagreement": False,
        }
    )


def _skip_model(rules: Triage, safety: dict) -> bool:
    backend = os.getenv("LLM_BACKEND", config.LLM_BACKEND).strip() or "RULES_ONLY"
    if backend.upper() == "RULES_ONLY":
        return True
    if safety.get("refusal"):
        return True
    if rules.trigger == INJURY_TRIGGER:
        return True
    return False


def combine(rules: Triage, proposal: LLMTriage) -> Triage:
    """Agree: keep the rules row. Disagree: take the model row and cap confidence at 0.6."""
    row_id = proposal.matrix_row_id.value
    row_category = _row_category(row_id)
    agreed = rules.trigger == row_id and rules.category == row_category
    meta = {
        "llm_trigger": row_id,
        "llm_category": row_category,
        "llm_confidence": proposal.confidence,
        "missing_fields": list(proposal.missing_fields),
        "decision_mode": "ensemble",
    }
    if agreed and rules.confidence >= config.CONF_ESCALATE:
        return rules.model_copy(
            update={**meta, "confidence": min(proposal.confidence, 0.95), "disagreement": False}
        )
    if agreed:
        return rules.model_copy(
            update={**meta, "confidence": min(proposal.confidence, 0.6), "disagreement": True}
        )
    entities = _merge_entities(rules, proposal)
    intent = _intent_for(row_category, proposal.intent, entities)
    chosen = _from_trigger(
        row_id,
        proposal.reasoning or rules.reasoning,
        entities,
        intent=intent,
        confidence=min(proposal.confidence, 0.6),
    )
    return chosen.model_copy(
        update={
            **meta,
            "disagreement": True,
            "rules_trigger": rules.rules_trigger,
            "rules_category": rules.rules_category,
            "rules_priority": rules.rules_priority,
            "confidence": min(float(proposal.confidence), 0.6),
        }
    )


def _row_category(trigger: str) -> str:
    if trigger == STANDARD_RETURN:
        return "Returns and Refunds"
    return matrix_row(trigger)["category"]


def _merge_entities(rules: Triage, proposal: LLMTriage) -> dict:
    entities = {
        "store_id": rules.store_id,
        "sku": rules.sku,
        "product_name": rules.product_name,
        "register_scope": rules.register_scope,
        "refund_amount": rules.refund_amount,
        "no_receipt": rules.no_receipt,
    }
    store = _valid_store(proposal.entities.store_id)
    if store:
        entities["store_id"] = store
    sku, name = _valid_sku(proposal.entities.sku)
    if sku:
        entities["sku"] = sku
        entities["product_name"] = name
    amount = proposal.entities.amount_inr
    if amount is not None and amount > 0:
        entities["refund_amount"] = float(amount)
    if proposal.entities.register_id and entities["register_scope"] != "all":
        entities["register_scope"] = "one"
    return entities


def _valid_store(value: str | None) -> str | None:
    if not value:
        return None
    token = value.strip().upper()
    if re.fullmatch(r"(?:ST|WH)\d{3}", token):
        return token
    return None


def _valid_sku(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    product = resolve_sku(str(value).strip())
    if product is None:
        return None, None
    return product["sku"], product["name"]


def _intent_for(category: str, llm_intent: str, entities: dict, text: str = "") -> str:
    if llm_intent == "policy_question":
        return ""
    if llm_intent == "analytics":
        return _analytics_subject(text, category)
    if category == "Inventory and Replenishment":
        return "stock_root_cause"
    if category == "Product Quality and Safety":
        return "quality_trend"
    if category == "Vendor and Supply Chain":
        return "short_shipments"
    amount = entities.get("refund_amount")
    if category == "Returns and Refunds" and (entities.get("no_receipt") or (amount is not None and amount >= 1000)):
        return "returns_over_threshold"
    return ""


def _analytics_subject(text: str, category: str) -> str:
    """Pick the pandas tool from what the question is about, not from the category alone."""
    glossed = apply_lexicon(text)
    if _is_vendor_ranking(glossed):
        return "vendor_quality_ranking"
    if re.search(r"fill rate", glossed, re.IGNORECASE) and re.search(
        r"lowest|worst|which", glossed, re.IGNORECASE
    ):
        return "lowest_fill_rate"
    if re.search(r"two or more|multiple stores|more than one store", glossed, re.IGNORECASE) and re.search(
        r"out of stock|stock-out|stockout|not available", glossed, re.IGNORECASE
    ):
        return "repeated_stockouts"
    if re.search(r"short shipment|received only", glossed, re.IGNORECASE):
        return "short_shipments"
    if re.search(r"last\s+\d+\s+hours|unresolved|grouped by store|open cases", glossed, re.IGNORECASE):
        return "open_high_priority"
    if re.search(r"root cause", glossed, re.IGNORECASE):
        return "stock_root_cause"
    if category == "Product Quality and Safety":
        if _has_quality_cue(glossed) and re.search(r"\b(vendor|supplier|brand)\b", glossed, re.IGNORECASE):
            return "vendor_quality_ranking"
        return "quality_trend"
    if category == "Inventory and Replenishment":
        return "stock_root_cause"
    if category == "Vendor and Supply Chain":
        return "short_shipments"
    return "open_high_priority"


def _from_trigger(
    trigger: str,
    reasoning: str,
    entities: dict,
    intent: str = "",
    confidence: float = 0.9,
) -> Triage:
    if trigger == STANDARD_RETURN:
        return Triage(
            category="Returns and Refunds",
            priority="P3",
            confidence=confidence,
            reasoning=reasoning,
            team="Store Manager",
            channel="returns_queue",
            sla_minutes=240,
            human_approval_required=False,
            policy_source="02_pos_pricing_returns_policy.md#returns-and-refunds",
            trigger=STANDARD_RETURN,
            intent=intent,
            needs_data=bool(intent),
            store_id=entities["store_id"],
            sku=entities["sku"],
            product_name=entities["product_name"],
            register_scope=entities["register_scope"],
            refund_amount=entities["refund_amount"],
            no_receipt=entities["no_receipt"],
        )
    return _from_matrix(trigger, reasoning, entities, intent=intent, confidence=confidence)


def _entities(text: str) -> dict:
    glossed = apply_lexicon(text)
    stores = [item.upper() for item in STORE_RE.findall(text)]
    amount_match = INR_RE.search(text)
    amount = float(amount_match.group(1).replace(",", "")) if amount_match else None
    product = resolve_sku(text)
    if re.search(r"\ball registers\b|store-wide|entire store", glossed, re.IGNORECASE):
        scope = "all"
    elif re.search(r"register\s*\d+|one register|card reader", glossed, re.IGNORECASE):
        scope = "one"
    else:
        scope = None
    return {
        "store_id": stores[0] if len(stores) == 1 else None,
        "sku": None if product is None else product["sku"],
        "product_name": None if product is None else product["name"],
        "register_scope": scope,
        "refund_amount": amount,
        "no_receipt": bool(re.search(r"without (a )?receipt|no[- ]receipt", glossed, re.IGNORECASE)),
    }


def _from_matrix(
    trigger: str,
    reasoning: str,
    entities: dict,
    intent: str = "",
    confidence: float = 0.93,
) -> Triage:
    row = matrix_row(trigger)
    return Triage(
        category=row["category"],
        priority=row["priority"],
        confidence=confidence,
        reasoning=reasoning,
        team=row["team"],
        channel=row["channel"],
        sla_minutes=row["sla_minutes"],
        human_approval_required=row["human_approval_required"],
        policy_source=row["policy_source"],
        trigger=row["trigger"],
        intent=intent,
        needs_data=bool(intent),
        store_id=entities["store_id"],
        sku=entities["sku"],
        product_name=entities["product_name"],
        register_scope=entities["register_scope"],
        refund_amount=entities["refund_amount"],
        no_receipt=entities["no_receipt"],
    )


def _check_security(text: str, safety: dict, entities: dict) -> Triage | None:
    if not (safety.get("injection") or safety.get("restricted")):
        return None
    return _from_matrix(
        "Restricted data, prompt injection, or suspicious request",
        "The message asks to override instructions or to reveal restricted data, so this is a security P1.",
        entities,
        confidence=0.97,
    )


def _check_injury(text: str, safety: dict, entities: dict) -> Triage | None:
    if not re.search(r"\binjur|\brecall\b|\bunsafe\b|\bhurt\b|hospital", text, re.IGNORECASE):
        return None
    return _from_matrix(
        "Contamination, injury, recall, or unsafe equipment",
        "The message reports injury, recall, or unsafe equipment, so this is a product-safety P1.",
        entities,
    )


def _check_storewide_pos(text: str, safety: dict, entities: dict) -> Triage | None:
    if not re.search(r"\ball registers\b|store-wide|entire store", text, re.IGNORECASE):
        return None
    if not re.search(r"card|payment|pos", text, re.IGNORECASE):
        return None
    return _from_matrix(
        "Multiple registers or store-wide payment outage",
        "Card payments are down across the store, so this is a POS P1 outage.",
        entities,
    )


def _check_one_register(text: str, safety: dict, entities: dict) -> Triage | None:
    card_reader = re.search(r"card reader", text, re.IGNORECASE)
    one_register = re.search(r"register\s*\d+", text, re.IGNORECASE) and re.search(
        r"card|payment|error|pos", text, re.IGNORECASE
    )
    if not card_reader and not one_register:
        return None
    return _from_matrix(
        "One register or one card reader failing",
        "One card reader or register is failing and the message does not say the whole store is down, so this is POS P3.",
        entities,
    )


def _check_vendor_ranking(text: str, safety: dict, entities: dict) -> Triage | None:
    if not _is_vendor_ranking(text):
        return None
    return _from_matrix(
        "Repeated quality complaints without immediate safety risk",
        "This is a vendor quality-complaint ranking, so it stays Product Quality and Safety at P2.",
        entities,
        intent="vendor_quality_ranking",
    )


def _check_open_cases(text: str, safety: dict, entities: dict) -> Triage | None:
    if not re.search(r"last 24 hours|unresolved|grouped by store", text, re.IGNORECASE):
        return None
    return _from_matrix(
        "General inquiry or analytics",
        "This asks for an unresolved-case summary, so it is an analytics request at P4.",
        entities,
        intent="open_high_priority",
    )


def _check_return_threshold(text: str, safety: dict, entities: dict) -> Triage | None:
    if not re.search(r"\breturn\b|\brefund\b", text, re.IGNORECASE):
        return None
    amount = entities["refund_amount"]
    high_value = amount is not None and amount >= 5000
    if not entities["no_receipt"] and not high_value:
        return None
    return _from_matrix(
        "No-receipt or high-value refund threshold",
        "The return is missing a receipt or is at the high-value line, so a manager must approve it and priority is P2.",
        entities,
        intent="returns_over_threshold",
    )


def _check_pricing(text: str, safety: dict, entities: dict) -> Triage | None:
    if not re.search(r"shelf|scans inr|price mismatch|label", text, re.IGNORECASE):
        return None
    if re.search(r"\b(many|multiple|department)\b", text, re.IGNORECASE):
        return _from_matrix(
            "Department or multi-customer pricing mismatch",
            "The price mismatch covers more than one SKU or many customers, so this is Pricing P2.",
            entities,
        )
    return _from_matrix(
        "Single SKU shelf-vs-register mismatch",
        "This is one shelf-versus-register price mismatch, so it is Pricing P3.",
        entities,
    )


def _check_quality(text: str, safety: dict, entities: dict) -> Triage | None:
    if not re.search(r"seam|defect|crack|quality complaint|split|stitch", text, re.IGNORECASE):
        return None
    return _from_matrix(
        "Repeated quality complaints without immediate safety risk",
        "Quality complaints are repeated and no injury or recall is stated, so this is Product Quality P2.",
        entities,
        intent="quality_trend",
    )


def _check_short_shipment(text: str, safety: dict, entities: dict) -> Triage | None:
    if not re.search(r"short shipment|received only|fill rate", text, re.IGNORECASE):
        return None
    return _from_matrix(
        "Repeated or below-90-percent short shipment",
        "The message is about a short shipment, so this routes to Supply Chain at P2.",
        entities,
        intent="short_shipments",
    )


def _is_vendor_ranking(text: str) -> bool:
    if re.search(r"which vendor|most .{0,40}quality complaints", text, re.IGNORECASE):
        return True
    party = re.search(r"\b(vendors?|suppliers?|brands?)\b", text, re.IGNORECASE)
    rank = re.search(r"\b(most|top|worst|highest)\b", text, re.IGNORECASE)
    return bool(party and rank and _has_quality_cue(text))


def _has_quality_cue(text: str) -> bool:
    return _quality_cue_pattern().search(text) is not None


def _quality_cue_pattern() -> re.Pattern:
    global _QUALITY_CUE
    if _QUALITY_CUE is not None:
        return _QUALITY_CUE
    phrases = [
        "cracked",
        "split",
        "warped",
        "torn",
        "missing padding",
        "missing protective padding",
        "unstable",
        "unsafe",
        "bad goods",
        "defective",
        "quality complaint",
        "quality complaints",
    ]
    reasons = load_frames()["returns_quality"]["reason"].dropna().astype(str)
    for reason in reasons.unique():
        if QUALITY_REASON.search(reason):
            phrases.append(reason.strip())
    ordered = sorted(set(phrases), key=len, reverse=True)
    _QUALITY_CUE = re.compile("|".join(re.escape(phrase) for phrase in ordered), re.IGNORECASE)
    return _QUALITY_CUE


def _check_stock(text: str, safety: dict, entities: dict) -> Triage | None:
    if not re.search(r"out of stock|not available|stock-out|stockout|reorder|root cause", text, re.IGNORECASE):
        return None
    if re.search(r"academy|warehouse|godown", text, re.IGNORECASE):
        trigger = "Warehouse stock depleted for high-demand or academy-order item"
        reasoning = "An academy or warehouse availability issue is an inventory P2 and uses the root-cause section."
    else:
        trigger = "High-demand SKU stock-out or false availability"
        reasoning = "A high-demand item is unavailable, so this is an inventory P2 stock-out."
    return _from_matrix(trigger, reasoning, entities, intent="stock_root_cause")


def _check_routine_return(text: str, safety: dict, entities: dict) -> Triage | None:
    if not re.search(r"\breturn\b|\brefund\b", text, re.IGNORECASE):
        return None
    # The matrix has no P3 returns row. The SOP says a standard return is P3.
    return Triage(
        category="Returns and Refunds",
        priority="P3",
        confidence=0.86,
        reasoning="This is a routine return with no no-receipt or high-value amount stated, so priority stays P3.",
        team="Store Manager",
        channel="returns_queue",
        sla_minutes=240,
        human_approval_required=False,
        policy_source="02_pos_pricing_returns_policy.md#returns-and-refunds",
        trigger="Standard return guidance",
        intent="",
        needs_data=False,
        store_id=entities["store_id"],
        sku=entities["sku"],
        product_name=entities["product_name"],
        register_scope=entities["register_scope"],
        refund_amount=entities["refund_amount"],
        no_receipt=entities["no_receipt"],
    )


def _check_service(text: str, safety: dict, entities: dict) -> Triage | None:
    if not re.search(r"\bupset\b|goodwill|service recovery", text, re.IGNORECASE):
        return None
    return _from_matrix(
        "Routine service recovery",
        "This is a customer-inconvenience note without a safety or payment outage, so it is Customer Service P3.",
        entities,
    )


def _fallback(entities: dict) -> Triage:
    row = matrix_row("General inquiry or analytics")
    return Triage(
        category=row["category"],
        priority=row["priority"],
        confidence=0.48,
        reasoning="No keyword rule matched this message, so confidence is low and a person should confirm the category.",
        team=row["team"],
        channel=row["channel"],
        sla_minutes=row["sla_minutes"],
        human_approval_required=row["human_approval_required"],
        policy_source=row["policy_source"],
        trigger=row["trigger"],
        intent="",
        needs_data=False,
        store_id=entities["store_id"],
        sku=entities["sku"],
        product_name=entities["product_name"],
        register_scope=entities["register_scope"],
        refund_amount=entities["refund_amount"],
        no_receipt=entities["no_receipt"],
    )


_CHECKS.extend(
    [
        _check_security,
        _check_injury,
        _check_storewide_pos,
        _check_one_register,
        _check_vendor_ranking,
        _check_open_cases,
        _check_return_threshold,
        _check_pricing,
        _check_quality,
        _check_short_shipment,
        _check_stock,
        _check_routine_return,
        _check_service,
    ]
)
