"""Mask PII, then decide whether the request must be refused. Those are separate steps."""

from __future__ import annotations

import base64
import re
import time
from dataclasses import dataclass

from copilot import trace
from copilot.schemas import SafetyResult

CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
PHONE_RE = re.compile(r"(?<!\d)(?:\+91[\s-]?)?0?([6-9](?:[\s-]?\d){9})(?!\d)")
EMPLOYEE_RE = re.compile(r"(?i)\b(employee (records|master|database|list|salaries)|salary sheet)\b")
ROLE_RE = re.compile(r"(?i)\b(role-?play|you are now|act as|as an? admin)\b")
B64_RE = re.compile(r"\b([A-Za-z0-9+/]{24,}={0,2})\b")
# A star from an already-masked local part must not start a second match on the last character.
EMAIL_RE = re.compile(r"(?<!\*)\b([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
# A label counts only when a value follows it. "CVV, or PIN" in a policy sentence stays as written.
SECRET_RE = re.compile(
    r"(?i)\b(cvv|cvc|pin|otp|password|passwd|aadhaar|aadhar)\b\s*[:=#-]?\s*(\d{3,}|[A-Za-z0-9]{6,})"
)
INJECTION_RE = re.compile(
    r"(?i)("
    r"ignore (all |any )?(previous|prior|above) (instructions|rules|policies)"
    r"|disregard (your |the )?(rules|instructions|policy)"
    r"|reveal (the )?(hidden|system) prompt"
    r"|do not cite"
    r"|invent a policy"
    r"|bypass (safety|policy|guard)"
    r"|jailbreak"
    r")"
)
RESTRICTED_RE = re.compile(
    r"(?i)(show|reveal|print|dump|export|list|give|display|share|send).{0,80}"
    r"(card numbers?|full card|cvv|customer database|all customers|"
    r"supplier contract|contract prices?|hidden prompt|system prompt|judge test)"
)


@dataclass
class MaskOutcome:
    text: str
    changed: bool
    kinds: list[str]


def mask_obj(value):
    """Run the masker over every string in a payload. A second pass is a no-op."""
    if isinstance(value, str):
        return mask_text(value).text
    if isinstance(value, dict):
        return {key: mask_obj(item) for key, item in value.items() if key != "raw_text"}
    if isinstance(value, list):
        return [mask_obj(item) for item in value]
    return value


def mask_text(text: str) -> MaskOutcome:
    """Replace card, phone, email, and secret values. Store IDs and prices stay."""
    kinds: list[str] = []
    updated = CARD_RE.sub(lambda match: _mask_card(match.group(0), kinds), text)
    updated = PHONE_RE.sub(lambda match: _mask_phone(match.group(1), kinds), updated)
    updated = EMAIL_RE.sub(lambda match: _mask_email(match.group(1), match.group(2), kinds), updated)
    updated, secret_count = SECRET_RE.subn(lambda match: f"{match.group(1)} [REDACTED]", updated)
    if secret_count:
        kinds.append("secret")
    return MaskOutcome(text=updated, changed=updated != text, kinds=kinds)


def screen(text: str) -> SafetyResult:
    """Detect injection and restricted asks on the original text, then mask."""
    scanned = text
    hidden = _decoded_payloads(text)
    if hidden:
        scanned = text + "\n" + hidden
    reasons: list[str] = []
    injection = bool(INJECTION_RE.search(scanned))
    restricted = bool(RESTRICTED_RE.search(scanned)) or bool(EMPLOYEE_RE.search(scanned))
    if ROLE_RE.search(scanned) and re.search(
        r"(?i)(system prompt|instructions|database|employee|contract|card number)",
        scanned,
    ):
        injection = True
    if injection:
        reasons.append("Prompt injection pattern.")
    if restricted:
        reasons.append("Request asks for restricted data.")
    masked = mask_text(text)
    if masked.changed:
        reasons.append("Masked " + ", ".join(masked.kinds) + ".")
    return SafetyResult(
        masked_text=masked.text,
        pii_masked=masked.changed,
        injection=injection,
        restricted=restricted,
        refusal=injection or restricted,
        reasons=reasons,
    )


def safety_node(state: dict) -> dict:
    started = time.perf_counter()
    result = screen(state.get("raw_text") or "")
    update = {
        "masked_text": result.masked_text,
        "safety": result.model_dump(),
        "raw_text": "",
    }
    update["trace"] = [
        trace.record(
            request_id=state.get("request_id", ""),
            agent="safety",
            mode="rule",
            started=started,
            input_summary=result.masked_text,
            output_summary=result.model_dump(),
        )
    ]
    return update


def _mask_card(raw: str, kinds: list[str]) -> str:
    digits = re.sub(r"\D", "", raw)
    if 13 <= len(digits) <= 19 and _luhn_ok(digits):
        kinds.append("card")
        return "[REDACTED_CARD]"
    return raw


def _mask_phone(national: str, kinds: list[str]) -> str:
    digits = re.sub(r"\D", "", national)
    kinds.append("phone")
    return "******" + digits[-4:]


def _decoded_payloads(text: str) -> str:
    """Decode long base64 tokens so an encoded instruction can be refused. The decoded text is not stored."""
    found: list[str] = []
    for match in B64_RE.finditer(text):
        token = match.group(1)
        padded = token + ("=" * ((4 - len(token) % 4) % 4))
        try:
            raw = base64.b64decode(padded, validate=True)
        except Exception:
            continue
        if not raw or len(raw) > 400:
            continue
        try:
            plain = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        letters = sum(character.isalpha() for character in plain)
        if letters < 8:
            continue
        found.append(plain)
    return "\n".join(found)


def _mask_email(local: str, domain: str, kinds: list[str]) -> str:
    kinds.append("email")
    if len(local) <= 1:
        hidden = "***"
    elif len(local) == 2:
        hidden = local[0] + "***"
    else:
        hidden = local[0] + ("*" * (len(local) - 2)) + local[-1]
    return f"{hidden}@{domain}"


def _luhn_ok(number: str) -> bool:
    total = 0
    for index, character in enumerate(reversed(number)):
        digit = int(character)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0
