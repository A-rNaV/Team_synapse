"""Escalate only on the four code gates, and write mock workflow JSON."""

from __future__ import annotations

import json
import time

from copilot import config, trace
from copilot.agents.safety import mask_obj
from copilot.schemas import Escalation, WorkflowPayload


def decide(triage: dict, safety: dict, retrieval: dict | None = None) -> Escalation:
    reasons = []
    if triage.get("priority") == "P1":
        reasons.append("Priority is P1.")
    if float(triage.get("confidence") or 0) < config.CONF_ESCALATE:
        reasons.append(f"Confidence is below {config.CONF_ESCALATE:.2f}.")
    if safety.get("injection") or safety.get("restricted"):
        reasons.append("The request is prompt injection or asks for restricted data.")
    if triage.get("human_approval_required"):
        reasons.append("The escalation matrix marks this trigger as human approval required.")
    if (retrieval or {}).get("weak"):
        reasons.append("Retrieval is weak, so a person should confirm the policy section.")
    if triage.get("decision_source") == "hard_rule" and triage.get("disagreement"):
        reasons.append("A hard rule conflicts with the draft decision.")
    required = bool(reasons)
    return Escalation(
        required=required,
        team=triage.get("team") if required else None,
        reason=" ".join(reasons) if required else None,
    )


def persist(request_id: str, escalation: Escalation, state: dict) -> None:
    triage = state.get("triage") or {}
    findings = state.get("data_findings") or {}
    summary = findings.get("summary") or {}
    ticket_id = f"MOCK-{request_id}"
    ticket = WorkflowPayload(
        kind="ticket",
        body={
            "ticket_id": ticket_id,
            "anchor_ts": config.NOW.strftime("%Y-%m-%d %H:%M:%S IST"),
            "persona": state.get("persona") or "",
            "store_id": triage.get("store_id"),
            "sku": triage.get("sku"),
            "category": triage.get("category"),
            "priority": triage.get("priority"),
            "team": escalation.team or triage.get("team"),
            "channel": triage.get("channel"),
            "sla_minutes": triage.get("sla_minutes"),
            "escalated": escalation.required,
            "reason": escalation.reason,
            "issue": state.get("masked_text") or "",
            "decision_source": triage.get("decision_source") or "",
            "data_tool": findings.get("tool") or "",
            "status": "mock_created",
        },
    )
    _write(f"{request_id}_ticket.json", ticket)
    if escalation.required:
        notify = WorkflowPayload(
            kind="notify",
            body={
                "ticket_id": ticket_id,
                "team": escalation.team,
                "channel": triage.get("channel"),
                "sla_minutes": triage.get("sla_minutes"),
                "message": escalation.reason,
            },
        )
        _write(f"{request_id}_notify.json", notify)
    if summary.get("vendor_claim"):
        claim = WorkflowPayload(
            kind="vendor_claim",
            body={
                "ticket_id": ticket_id,
                "submitted": False,
                "vendor_id": summary.get("vendor_id"),
                "store_id": triage.get("store_id") or summary.get("store_id"),
                "sku": triage.get("sku") or summary.get("sku"),
                "evidence": findings.get("facts") or [],
                "note": "Draft only. A human must approve before a vendor claim is submitted.",
            },
        )
        _write(f"{request_id}_vendor_claim.json", claim)
    if (state.get("safety") or {}).get("refusal"):
        alert = WorkflowPayload(
            kind="security_alert",
            body={
                "ticket_id": ticket_id,
                "alert": "security_alert",
                "team": "Security",
                "issue": state.get("masked_text") or "",
                "reason": "Restricted or injection request.",
            },
        )
        _write(f"{request_id}_security_alert.json", alert)


def escalation_node(state: dict) -> dict:
    started = time.perf_counter()
    decision = decide(
        state.get("triage") or {},
        state.get("safety") or {},
        state.get("retrieval") or {},
    )
    request_id = _safe_id(state.get("request_id") or "request")
    persist(request_id, decision, state)
    update = {"escalation": decision.model_dump()}
    update["trace"] = [
        trace.record(
            request_id=request_id,
            agent="escalation",
            mode="rule",
            started=started,
            input_summary={
                "priority": (state.get("triage") or {}).get("priority"),
                "confidence": (state.get("triage") or {}).get("confidence"),
                "human_approval_required": (state.get("triage") or {}).get("human_approval_required"),
            },
            output_summary=decision.model_dump(),
        )
    ]
    return update


def _write(filename: str, payload: WorkflowPayload) -> None:
    config.OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    path = config.OUTBOX_DIR / filename
    body = mask_obj(payload.model_dump())
    path.write_text(json.dumps(body, indent=2), encoding="utf-8")


def _safe_id(request_id: str) -> str:
    cleaned = "".join(character for character in request_id if character.isalnum() or character in "-_")
    return cleaned or "request"
