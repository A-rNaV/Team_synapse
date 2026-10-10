"""Pydantic models for one copilot turn. Field names follow guide section 14."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Category = Literal[
    "POS and Payments",
    "Inventory and Replenishment",
    "Pricing and Promotions",
    "Returns and Refunds",
    "Vendor and Supply Chain",
    "Product Quality and Safety",
    "Customer Service",
    "Other or Security",
]
Priority = Literal["P1", "P2", "P3", "P4"]


class UserRequest(BaseModel):
    text: str
    persona: str | None = None
    request_id: str | None = None


class SafetyResult(BaseModel):
    masked_text: str
    pii_masked: bool
    injection: bool
    restricted: bool
    refusal: bool
    reasons: list[str] = Field(default_factory=list)


class Triage(BaseModel):
    category: Category
    priority: Priority
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    team: str
    channel: str
    sla_minutes: int
    human_approval_required: bool
    policy_source: str
    trigger: str
    intent: str = ""
    needs_data: bool = False
    store_id: str | None = None
    sku: str | None = None
    product_name: str | None = None
    register_scope: str | None = None
    refund_amount: float | None = None
    no_receipt: bool = False
    disagreement: bool = False
    decision_mode: str = "rule"
    rules_trigger: str = ""
    rules_category: str = ""
    rules_priority: str = ""
    llm_trigger: str = ""
    llm_category: str = ""
    llm_confidence: float | None = None
    missing_fields: list[str] = Field(default_factory=list)
    decision_source: str = "rule"
    knn_confidence: float | None = None
    neighbours: list[dict] = Field(default_factory=list)
    llm_called: bool = False


class MatrixRowId(str, Enum):
    """Escalation-matrix triggers, plus the SOP routine-return id the matrix does not list."""

    one_register = "One register or one card reader failing"
    storewide = "Multiple registers or store-wide payment outage"
    payment_data = "Payment data or credential request"
    single_price = "Single SKU shelf-vs-register mismatch"
    multi_price = "Department or multi-customer pricing mismatch"
    refund_threshold = "No-receipt or high-value refund threshold"
    stockout = "High-demand SKU stock-out or false availability"
    reorder = "Routine reorder or cycle count"
    warehouse = "Warehouse stock depleted for high-demand or academy-order item"
    short_ship = "Repeated or below-90-percent short shipment"
    quality = "Repeated quality complaints without immediate safety risk"
    injury = "Contamination, injury, recall, or unsafe equipment"
    service = "Routine service recovery"
    restricted = "Restricted data, prompt injection, or suspicious request"
    analytics = "General inquiry or analytics"
    standard_return = "Standard return guidance"


class LLMEntities(BaseModel):
    store_id: str | None = None
    sku: str | None = None
    register_id: str | None = None
    amount_inr: float | None = None

    @field_validator("store_id", "sku", "register_id", mode="before")
    @classmethod
    def _blank_text(cls, value):
        if value is None:
            return None
        text = str(value).strip()
        if text.lower() in {"", "none", "null", "n/a", "unknown", "na"}:
            return None
        return text

    @field_validator("amount_inr", mode="before")
    @classmethod
    def _amount(cls, value):
        if value is None or value == "":
            return None
        if isinstance(value, str):
            cleaned = value.replace(",", "").replace("INR", "").replace("inr", "").strip()
            if cleaned.lower() in {"", "none", "null", "n/a", "unknown"}:
                return None
            return float(cleaned)
        return value


class LLMTriage(BaseModel):
    category: Category
    matrix_row_id: MatrixRowId
    entities: LLMEntities = Field(default_factory=LLMEntities)
    intent: Literal["triage", "analytics", "policy_question"]
    confidence: float = Field(ge=0, le=1)
    reasoning: str = ""
    missing_fields: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data):
        if not isinstance(data, dict):
            return data
        row = data.get("matrix_row_id", data.get("matrixRowId", data.get("trigger")))
        if isinstance(row, str):
            cleaned = row.strip().strip('"')
            for item in MatrixRowId:
                if item.value.lower() == cleaned.lower():
                    cleaned = item.value
                    break
            data["matrix_row_id"] = cleaned
        category = data.get("category")
        if isinstance(category, str):
            for allowed in (
                "POS and Payments",
                "Inventory and Replenishment",
                "Pricing and Promotions",
                "Returns and Refunds",
                "Vendor and Supply Chain",
                "Product Quality and Safety",
                "Customer Service",
                "Other or Security",
            ):
                if category.strip().lower() == allowed.lower():
                    data["category"] = allowed
                    break
        entities = data.get("entities")
        if isinstance(entities, str):
            entities = {}
        if not isinstance(entities, dict):
            entities = {}
        for key in ("store_id", "sku", "register_id", "amount_inr"):
            if key not in entities and key in data:
                entities[key] = data[key]
        data["entities"] = entities
        intent = str(data.get("intent") or "").strip().lower().replace("-", "_").replace(" ", "_")
        intent_aliases = {
            "triage": "triage",
            "operational": "triage",
            "operations": "triage",
            "ops": "triage",
            "analytics": "analytics",
            "analytic": "analytics",
            "analysis": "analytics",
            "policy_question": "policy_question",
            "policy": "policy_question",
            "question": "policy_question",
        }
        if intent in intent_aliases:
            data["intent"] = intent_aliases[intent]
        confidence = data.get("confidence")
        if isinstance(confidence, str):
            confidence = confidence.strip().rstrip("%")
            if confidence:
                confidence = float(confidence)
        if isinstance(confidence, (int, float)) and confidence > 1 and confidence <= 100:
            data["confidence"] = float(confidence) / 100.0
        missing = data.get("missing_fields", data.get("missingFields"))
        if missing is None:
            data["missing_fields"] = []
        elif isinstance(missing, str):
            data["missing_fields"] = [part.strip() for part in missing.split(",") if part.strip()]
        elif isinstance(missing, list):
            data["missing_fields"] = [str(part) for part in missing if str(part).strip()]
        return data


class Chunk(BaseModel):
    id: str
    source: str
    heading: str
    text: str


class Retrieval(BaseModel):
    query: str
    chunks: list[Chunk] = Field(default_factory=list)
    weak: bool = False
    scores: list[dict] = Field(default_factory=list)


class RootCause(BaseModel):
    store_id: str | None = None
    sku: str | None = None
    likely_cause: str
    evidence: list[str] = Field(default_factory=list)


class DataFindings(BaseModel):
    tool: str = ""
    files: list[str] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)


class Escalation(BaseModel):
    required: bool
    team: str | None = None
    reason: str | None = None


class WorkflowPayload(BaseModel):
    kind: Literal["ticket", "notify", "vendor_claim"]
    body: dict


class CopilotResponse(BaseModel):
    category: Category
    priority: Priority
    confidence: float = Field(ge=0, le=1)
    answer: str
    citations: list[str]
    data_used: list[str] = Field(default_factory=list)
    escalation: Escalation
    pii_masked: bool
    follow_up_question: str | None = None
    safety_refusal: bool = False


class CopilotState(BaseModel):
    request_id: str = ""
    persona: str = ""
    raw_text: str = ""
    masked_text: str = ""
    safety: SafetyResult | None = None
    triage: Triage | None = None
    retrieval: Retrieval | None = None
    data_findings: DataFindings | None = None
    escalation: Escalation | None = None
    response: CopilotResponse | None = None
    trace: list[dict] = Field(default_factory=list)
