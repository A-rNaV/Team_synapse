"""Build the answer from retrieved sections and pandas facts. Drop any citation that was not retrieved."""

from __future__ import annotations

import re
import time

from copilot import trace
from copilot.agents.safety import mask_text
from copilot.schemas import CopilotResponse, Escalation

# One short statement per section. Shown only when that section was retrieved.
POLICY_LINES = {
    "01_retail_operations_sop.md#priority-rules": (
        "P1 needs immediate human escalation. Use it for a store-wide POS or payment outage, a payment-data request, "
        "product safety or recall, injury risk, or unsafe equipment."
    ),
    "01_retail_operations_sop.md#analytics-rule": (
        "Figures below come from the CSV files. Last 24 hours and last 30 days are counted from "
        "2026-10-10 12:00:00 IST."
    ),
    "02_pos_pricing_returns_policy.md#pos-card-reader-runbook": (
        "One failing card reader, with other registers working, is P3. Re-seat or restart the reader, try another "
        "approved register, use an approved alternate tender if store policy allows, and open a POS ticket with store ID, "
        "register ID, error code, and start time. Do not collect full card numbers, CVV, or PIN."
    ),
    "02_pos_pricing_returns_policy.md#payment-security": (
        "Requests for card numbers, CVV, payment tokens, passwords, or POS credentials are refused. "
        "Do not write card details down or send them in chat."
    ),
    "02_pos_pricing_returns_policy.md#pricing-and-promotions": (
        "An isolated shelf-versus-register mismatch is usually P3. Verify the shelf label, POS price, SKU, and "
        "promotion dates. If the shelf label is lower and current, follow that lower displayed price within "
        "manager-approved limits, correct the label, and open a pricing ticket. Do not invent promotion terms."
    ),
    "02_pos_pricing_returns_policy.md#returns-and-refunds": (
        "A standard return with a receipt is P3. A no-receipt return needs manager review. A refund of INR 5000 or "
        "more needs manager approval, and a no-receipt refund of INR 1000 or more also needs manager approval. "
        "The assistant must not approve the refund or override POS."
    ),
    "05_responsible_ai_policy.md#human-in-the-loop": (
        "A human must approve refund overrides, product quarantine, vendor-claim submission, and other "
        "approval-required actions. The assistant can prepare the summary only."
    ),
    "05_responsible_ai_policy.md#pii-and-payment-data-masking": (
        "Phone numbers, emails, and card numbers are masked before they are stored. A card becomes [REDACTED_CARD]. "
        "These values are not needed on a return ticket."
    ),
    "05_responsible_ai_policy.md#prompt-injection": (
        "Instructions to ignore policy, reveal hidden prompts, or expose private data are refused. "
        "The safe alternative is an ordinary store-operations question."
    ),
    "03_inventory_replenishment_policy.md#stock-outs-and-replenishment": (
        "On-hand at or below the reorder point is below the reorder threshold. Zero on-hand for a high-demand item "
        "is P2, and receipts plus vendor fill rate should be checked before anyone promises availability."
    ),
    "03_inventory_replenishment_policy.md#root-cause-hints": (
        "Stock-out review checks on-hand, system quantity, reorder point, recent receipts, vendor fill rate, and "
        "related cases, in that order. Say 'likely linked to' and do not assign blame without evidence."
    ),
    "04_vendor_quality_policy.md#short-shipments": (
        "A short shipment means received quantity is below ordered quantity. Below 90 percent on a high-demand item "
        "is P2 for Supply Chain. Two consecutive short receipts call for vendor-claim review. "
        "The assistant must not submit the claim."
    ),
    "04_vendor_quality_policy.md#vendor-performance": (
        "Fill rate below 80 percent or on-time rate below 85 percent is a warning signal. It is not proof of fault."
    ),
    "04_vendor_quality_policy.md#product-quality-complaints": (
        "Repeated quality complaints with no immediate safety risk are P2: hold the affected stock for review and "
        "send it to the Store Manager and Product Quality. Injury, recall, or unsafe equipment is P1 and means "
        "quarantine plus escalation. Do not decide the product is safe, and do not accuse the vendor."
    ),
}


def build(state: dict) -> CopilotResponse:
    safety = state.get("safety") or {}
    triage = state.get("triage") or {}
    retrieval = state.get("retrieval") or {}
    findings = state.get("data_findings") or {}
    escalation = Escalation.model_validate(state.get("escalation") or {"required": False})
    retrieved_ids = [chunk["id"] for chunk in retrieval.get("chunks") or []]
    allowed = set(retrieved_ids)

    if safety.get("refusal"):
        parts = ["I have to refuse this request."]
    else:
        parts = [triage.get("reasoning") or "I classified the request from the keyword rules."]
        if safety.get("pii_masked"):
            parts.append("Stored text after masking: " + (state.get("masked_text") or ""))
        parts.extend(findings.get("facts") or [])
        if (findings.get("summary") or {}).get("vendor_claim"):
            parts.append("A draft vendor-claim file was written and was not submitted.")

    cited: list[str] = []
    for chunk_id in retrieved_ids:
        line = _policy_line(chunk_id, triage)
        if line and chunk_id not in cited:
            parts.append(line)
            cited.append(chunk_id)

    retrieval_weak = bool(retrieval.get("weak"))
    if retrieval_weak and (triage.get("category") == "Other or Security" or not cited) and not safety.get("refusal"):
        parts.append("I cannot confirm the policy from the available documents.")
    elif not cited and not safety.get("refusal"):
        parts.append("I cannot confirm the policy from the available documents.")
        escalation = Escalation(
            required=True,
            team=escalation.team or triage.get("team"),
            reason="No supporting policy section was retrieved.",
        )

    if escalation.required:
        parts.append(f"Escalated to {escalation.team}. {escalation.reason}")

    answer = " ".join(part.strip() for part in parts if part and str(part).strip())
    answer, cited, pii_masked = verify(answer, cited, allowed, bool(safety.get("pii_masked")))
    follow_up = follow_up_question(state.get("masked_text") or "", safety, triage)
    if retrieval_weak and not follow_up:
        follow_up = "Which store issue should I look up in the policy documents?"
    return CopilotResponse(
        category=triage.get("category") or "Other or Security",
        priority=triage.get("priority") or "P4",
        confidence=float(triage.get("confidence") or 0),
        answer=answer,
        citations=cited,
        data_used=list(findings.get("files") or []),
        escalation=escalation,
        pii_masked=pii_masked,
        follow_up_question=follow_up,
        safety_refusal=bool(safety.get("refusal")),
    )


def _policy_line(chunk_id: str, triage: dict) -> str | None:
    if chunk_id == "02_pos_pricing_returns_policy.md#pos-card-reader-runbook" and triage.get("priority") == "P1":
        return (
            "The whole store cannot take card payments, so this is P1. Escalate to the Store Manager and POS Support now. "
            "Share the store ID and the time it started. Do not collect full card numbers, CVV, or PIN."
        )
    return POLICY_LINES.get(chunk_id)


def verify(answer: str, citations: list[str], allowed: set[str], already_masked: bool) -> tuple[str, list[str], bool]:
    """Drop citations that were not retrieved, then mask any PII that reached the answer."""
    kept = [citation for citation in citations if citation in allowed]
    masked = mask_text(answer)
    return masked.text, kept, already_masked or masked.changed


def follow_up_question(text: str, safety: dict, triage: dict) -> str | None:
    if safety.get("refusal"):
        return "What store operations question can I help with instead?"
    question = _missing_question(text, triage)
    if triage.get("disagreement"):
        return question or (
            "I am not fully sure I classified this correctly. "
            "What exactly happened, and which store or product is involved?"
        )
    if triage.get("intent") in {"open_high_priority", "vendor_quality_ranking"}:
        return None
    return question


def _missing_question(text: str, triage: dict) -> str | None:
    missing = []
    if not triage.get("store_id"):
        if re.search(r"two stores|multiple stores|several stores", text, re.IGNORECASE):
            missing.append("store IDs")
        else:
            missing.append("store ID")
    needs_product = triage.get("category") in {
        "Inventory and Replenishment",
        "Pricing and Promotions",
        "Product Quality and Safety",
        "Returns and Refunds",
        "Vendor and Supply Chain",
    }
    if needs_product and not triage.get("sku"):
        missing.append("SKU or product name")
    if triage.get("category") == "POS and Payments" and not triage.get("register_scope"):
        missing.append("whether one register or the whole store is affected")
    if not missing:
        return None
    if missing == ["store ID"]:
        return "Which store ID is affected?"
    if missing == ["store IDs"]:
        return "Which store IDs are affected?"
    if missing == ["store ID", "SKU or product name"] or missing == ["store IDs", "SKU or product name"]:
        return "Which store and SKU are affected?"
    return "Which " + " and ".join(missing) + " should I use?"


def composer_node(state: dict) -> dict:
    started = time.perf_counter()
    response = build(state)
    update = {"response": response.model_dump()}
    update["trace"] = [
        trace.record(
            request_id=state.get("request_id", ""),
            agent="composer",
            mode="rule",
            started=started,
            input_summary={"chunk_ids": [chunk["id"] for chunk in (state.get("retrieval") or {}).get("chunks") or []]},
            output_summary={
                "category": response.category,
                "priority": response.priority,
                "citations": response.citations,
                "escalated": response.escalation.required,
                "safety_refusal": response.safety_refusal,
                "pii_masked": response.pii_masked,
            },
        )
    ]
    return update
