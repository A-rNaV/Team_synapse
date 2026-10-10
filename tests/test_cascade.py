from copilot.agents.escalation import escalation_node, persist
from copilot.agents.retrieval import retrieval_node
from copilot.agents.safety import mask_text, safety_node
from copilot.agents.triage import classify
from copilot.graph import run_turn
from copilot.knn import KnnHit
from copilot.schemas import Escalation, Retrieval


def _hit() -> KnnHit:
    return KnnHit(
        trigger="One register or one card reader failing",
        category="POS and Payments",
        priority="P3",
        confidence=0.91,
        top1=0.88,
        neighbours=[
            {
                "case_id": "RET-001",
                "text": "Card reader on register 4 shows error 51.",
                "category": "POS and Payments",
                "priority": "P3",
                "row": "One register or one card reader failing",
                "store": "ST003",
                "sku": "",
                "similarity": 0.88,
            }
        ],
    )


def test_accepted_knn_does_not_call_the_model(monkeypatch):
    monkeypatch.setenv("TRIAGE_PATH", "cascade")
    monkeypatch.setenv("LLM_BACKEND", "deepseek")
    monkeypatch.setattr("copilot.agents.triage._knn_hit", lambda text: _hit())
    monkeypatch.setattr("copilot.agents.triage._knn_thresholds", lambda: (0.75, 0.85))

    def boom(text, neighbours=None):
        raise AssertionError(text)

    monkeypatch.setattr("copilot.agents.triage.propose", boom)
    decision = classify("Card reader on register 4 is showing error 51, but other registers are working.", {})
    assert decision.decision_source == "knn"
    assert decision.category == "POS and Payments"
    assert decision.priority == "P3"
    assert decision.neighbours[0]["case_id"] == "RET-001"
    assert not decision.llm_called


def test_nodes_write_only_their_own_keys(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_BACKEND", "RULES_ONLY")
    monkeypatch.setenv("TRIAGE_PATH", "cascade")
    monkeypatch.setattr("copilot.agents.triage._knn_hit", lambda text: None)
    monkeypatch.setattr("copilot.agents.escalation.config.OUTBOX_DIR", tmp_path)
    monkeypatch.setattr("copilot.trace.LOG_PATH", tmp_path / "trace.jsonl")
    monkeypatch.setattr(
        "copilot.agents.retrieval.gather",
        lambda text, triage, safety: Retrieval(query=text, chunks=[], weak=False, scores=[]),
    )
    state = {
        "request_id": "node-keys",
        "persona": "Cashier",
        "raw_text": "Card reader on register 4 is showing error 51.",
        "masked_text": "",
        "trace": [],
    }
    safety = safety_node(state)
    assert set(safety) <= {"masked_text", "safety", "raw_text", "trace"}
    state.update({key: value for key, value in safety.items() if key != "trace"})
    from copilot.agents.triage import triage_node
    from copilot.agents.data_agent import data_node
    from copilot.agents.composer import composer_node

    triage = triage_node(state)
    assert set(triage) <= {"triage", "trace"}
    state.update({key: value for key, value in triage.items() if key != "trace"})
    retrieval = retrieval_node(state)
    assert set(retrieval) <= {"retrieval", "trace"}
    state.update({key: value for key, value in retrieval.items() if key != "trace"})
    data = data_node(state)
    assert set(data) <= {"data_findings", "trace"}
    state.update({key: value for key, value in data.items() if key != "trace"})
    escalation = escalation_node(state)
    assert set(escalation) <= {"escalation", "trace"}
    state.update({key: value for key, value in escalation.items() if key != "trace"})
    composer = composer_node(state)
    assert set(composer) <= {"response", "trace"}


def test_outbox_and_trace_mask_email(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_BACKEND", "RULES_ONLY")
    monkeypatch.setenv("TRIAGE_PATH", "cascade")
    monkeypatch.setattr("copilot.agents.triage._knn_hit", lambda text: None)
    monkeypatch.setattr("copilot.agents.escalation.config.OUTBOX_DIR", tmp_path)
    monkeypatch.setattr("copilot.trace.LOG_PATH", tmp_path / "trace.jsonl")
    monkeypatch.setattr(
        "copilot.agents.retrieval.gather",
        lambda text, triage, safety: Retrieval(query=text, chunks=[], weak=False, scores=[]),
    )
    run_turn(
        "Shelf label says Match Football is 899 but the till shows 1099. Mail customer.name@example.com when fixed.",
        persona="Cashier",
        request_id="pii-check",
    )
    blob = "\n".join(path.read_text(encoding="utf-8") for path in tmp_path.rglob("*") if path.is_file())
    assert "customer.name@example.com" not in blob
    assert not mask_text(blob).changed


def test_same_prompt_twice_is_identical(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "RULES_ONLY")
    monkeypatch.setenv("TRIAGE_PATH", "cascade")
    monkeypatch.setattr("copilot.agents.triage._knn_hit", lambda text: _hit())
    monkeypatch.setattr("copilot.agents.triage._knn_thresholds", lambda: (0.75, 0.85))
    monkeypatch.setattr(
        "copilot.agents.retrieval.gather",
        lambda text, triage, safety: Retrieval(query=text, chunks=[], weak=False, scores=[]),
    )
    first, _trace_a = run_turn("Card reader on register 4 is showing error 51.", request_id="same-a")
    second, _trace_b = run_turn("Card reader on register 4 is showing error 51.", request_id="same-b")
    assert first.model_dump() == second.model_dump()


def test_payload_built_from_raw_email_is_masked(tmp_path, monkeypatch):
    monkeypatch.setattr("copilot.agents.escalation.config.OUTBOX_DIR", tmp_path)
    persist(
        "raw-email",
        Escalation(required=False),
        {
            "masked_text": "Mail customer.name@example.com when fixed.",
            "persona": "Cashier",
            "triage": {"category": "Pricing and Promotions", "priority": "P3", "team": "Store Manager"},
            "safety": {},
            "data_findings": {},
        },
    )
    written = (tmp_path / "raw-email_ticket.json").read_text(encoding="utf-8")
    assert "customer.name@example.com" not in written
    assert not mask_text(written).changed
