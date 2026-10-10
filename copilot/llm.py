"""One LLM adapter. Rules-only mode never calls it.

Backends: deepseek, openai, gemini, groq, ollama, and RULES_ONLY.
Temperature is 0. The reply must validate as JSON against a Pydantic model.
On a bad reply the adapter tries once more, then returns `fallback` if given.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import urllib.error
import urllib.request
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from copilot.config import LLM_BACKEND, ROOT

CACHE_DIR = ROOT / ".cache"
PROMPT_SALT = "uc3-json-v1"
_USAGE_LOCAL = threading.local()
_CACHE_LOCK = threading.Lock()

T = TypeVar("T", bound=BaseModel)


class LLMUnavailable(RuntimeError):
    """Raised when no model reply could be validated and no fallback was given."""


def reset_llm_usage() -> None:
    """Zero this thread's call counter. RULES_ONLY never increments it."""
    _USAGE_LOCAL.calls = 0
    _USAGE_LOCAL.tokens = 0


def llm_usage() -> dict:
    return {
        "calls": int(getattr(_USAGE_LOCAL, "calls", 0)),
        "tokens": int(getattr(_USAGE_LOCAL, "tokens", 0)),
    }


def _add_usage(*, calls: int = 0, tokens: int = 0) -> None:
    _USAGE_LOCAL.calls = int(getattr(_USAGE_LOCAL, "calls", 0)) + calls
    _USAGE_LOCAL.tokens = int(getattr(_USAGE_LOCAL, "tokens", 0)) + tokens


def complete_json(
    system: str,
    user: str,
    model: type[T],
    fallback: T | None = None,
) -> T:
    """Return a validated model. RULES_ONLY skips the network and uses fallback."""
    backend = os.getenv("LLM_BACKEND", LLM_BACKEND).strip() or "RULES_ONLY"
    if backend.upper() == "RULES_ONLY":
        if fallback is not None:
            return fallback
        raise LLMUnavailable("RULES_ONLY has no model. Pass a rules fallback or switch LLM_BACKEND.")

    model_name = _model_name(backend.lower())
    cache_path = _cache_path(backend.lower(), model_name, system, user)
    cached = _read_cache(cache_path, model)
    if cached is not None:
        return cached

    last_error: Exception | None = None
    attempt_user = user
    for _attempt in range(2):
        try:
            raw = _call_backend(backend.lower(), system, attempt_user)
            result = model.model_validate(_parse_json(raw))
            _write_cache(cache_path, result)
            return result
        except KeyError as exc:
            raise LLMUnavailable(f"{backend} API key is not set ({exc}).") from exc
        except (LLMUnavailable, ValidationError, ValueError, urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            attempt_user = (
                user
                + "\n\nThe previous JSON failed validation: "
                + str(exc)[:800]
                + "\nReturn one JSON object only."
            )
    if fallback is not None:
        return fallback
    raise LLMUnavailable(f"{backend} failed after 2 attempts: {last_error}")


def _call_backend(backend: str, system: str, user: str) -> str:
    _add_usage(calls=1)
    if backend == "deepseek":
        return _openai_compatible(
            base=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            api_key=os.environ["DEEPSEEK_API_KEY"],
            model=os.getenv("LLM_MODEL") or os.getenv("DEEPSEEK_MODEL") or "deepseek-flash",
            system=system,
            user=user,
        )
    if backend == "openai":
        return _openai_compatible(
            base=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.environ["OPENAI_API_KEY"],
            model=os.getenv("LLM_MODEL") or "gpt-4o-mini",
            system=system,
            user=user,
        )
    if backend == "groq":
        return _openai_compatible(
            base=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            api_key=os.environ["GROQ_API_KEY"],
            model=os.getenv("LLM_MODEL") or os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile",
            system=system,
            user=user,
        )
    if backend == "gemini":
        return _gemini(system, user)
    if backend == "ollama":
        return _ollama(system, user)
    raise LLMUnavailable(
        f"Unknown LLM_BACKEND '{backend}'. Use deepseek, openai, gemini, groq, ollama, or RULES_ONLY."
    )


def _openai_compatible(base: str, api_key: str, model: str, system: str, user: str) -> str:
    body = {
        "model": model,
        "temperature": 0,
        "max_tokens": 250,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    # Flash spends the token budget on hidden reasoning unless this is set,
    # and the JSON classification is then cut off.
    if "deepseek" in model.lower() or "deepseek" in base.lower():
        body["thinking"] = {"type": "disabled"}
    payload = _post_json(
        base.rstrip("/") + "/chat/completions",
        body,
        {"Authorization": f"Bearer {api_key}"},
    )
    return payload["choices"][0]["message"]["content"]


def _gemini(system: str, user: str) -> str:
    model = os.getenv("LLM_MODEL") or os.getenv("GEMINI_MODEL") or "gemini-2.0-flash"
    key = os.environ["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }
    payload = _post_json(url, body, {})
    return payload["candidates"][0]["content"]["parts"][0]["text"]


def _ollama(system: str, user: str) -> str:
    base = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("LLM_MODEL") or os.getenv("OLLAMA_MODEL") or "llama3.2"
    body = {
        "model": model,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    payload = _post_json(base + "/api/chat", body, {})
    return payload["message"]["content"]


def _post_json(url: str, body: dict, headers: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    usage = payload.get("usage") or {}
    total = usage.get("total_tokens")
    if total is None:
        total = int(usage.get("prompt_tokens") or 0) + int(usage.get("completion_tokens") or 0)
    _add_usage(tokens=int(total or 0))
    return payload


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("Model reply did not contain a JSON object.")
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("Model JSON was not an object.")
    return parsed


def _model_name(backend: str) -> str:
    if backend == "deepseek":
        return os.getenv("LLM_MODEL") or os.getenv("DEEPSEEK_MODEL") or "deepseek-flash"
    if backend == "openai":
        return os.getenv("LLM_MODEL") or "gpt-4o-mini"
    if backend == "groq":
        return os.getenv("LLM_MODEL") or os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile"
    if backend == "gemini":
        return os.getenv("LLM_MODEL") or os.getenv("GEMINI_MODEL") or "gemini-2.0-flash"
    if backend == "ollama":
        return os.getenv("LLM_MODEL") or os.getenv("OLLAMA_MODEL") or "llama3.2"
    return os.getenv("LLM_MODEL") or backend


def _cache_path(backend: str, model_name: str, system: str, user: str):
    digest = hashlib.sha256()
    digest.update(PROMPT_SALT.encode("utf-8"))
    for part in (backend, model_name, system, user):
        digest.update(b"\0")
        digest.update(part.encode("utf-8"))
    return CACHE_DIR / f"{digest.hexdigest()}.json"


def _read_cache(path, model: type[T]) -> T | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return model.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValidationError, ValueError):
        return None


def _write_cache(path, result: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result.model_dump(mode="json"), ensure_ascii=True)
    temporary = path.with_suffix(path.suffix + f".{threading.get_ident()}.tmp")
    with _CACHE_LOCK:
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(path)
