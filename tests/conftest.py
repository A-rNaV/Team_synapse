import pytest

from copilot.llm import LLMUnavailable


@pytest.fixture(autouse=True)
def _offline_and_sandboxed(monkeypatch, tmp_path):
    """No test reaches a live model, reads cached replies, or writes to the real outbox and trace."""

    def _no_network(backend, system, user):
        raise LLMUnavailable("Tests do not call a live model. Mock propose or _call_backend instead.")

    monkeypatch.setattr("copilot.llm._call_backend", _no_network)
    monkeypatch.setattr("copilot.llm.CACHE_DIR", tmp_path / "llm_cache")
    monkeypatch.setattr("copilot.config.OUTBOX_DIR", tmp_path / "outbox")
    monkeypatch.setattr("copilot.trace.LOG_PATH", tmp_path / "logs" / "trace.jsonl")
