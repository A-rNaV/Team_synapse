"""LangGraph wiring. Each node is also safe to call from the sequential runner."""

from __future__ import annotations

import operator
import uuid
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from copilot.agents.composer import composer_node
from copilot.agents.data_agent import data_node
from copilot.agents.escalation import escalation_node
from copilot.agents.retrieval import retrieval_node
from copilot.agents.safety import safety_node
from copilot.agents.triage import triage_node
from copilot.schemas import CopilotResponse, CopilotState

NODE_ORDER = (
    ("safety", safety_node),
    ("triage", triage_node),
    ("retrieval", retrieval_node),
    ("data", data_node),
    ("escalation", escalation_node),
    ("composer", composer_node),
)


class GraphState(TypedDict, total=False):
    request_id: str
    persona: str
    raw_text: str
    masked_text: str
    safety: dict
    triage: dict
    retrieval: dict
    data_findings: dict
    escalation: dict
    response: dict
    trace: Annotated[list, operator.add]


_COMPILED = None


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("safety", safety_node)
    graph.add_node("triage", triage_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("data", data_node)
    graph.add_node("escalation", escalation_node)
    graph.add_node("composer", composer_node)
    graph.add_edge(START, "safety")
    graph.add_edge("safety", "triage")
    graph.add_edge("triage", "retrieval")
    graph.add_edge("triage", "data")
    graph.add_edge("retrieval", "escalation")
    graph.add_edge("data", "escalation")
    graph.add_edge("escalation", "composer")
    graph.add_edge("composer", END)
    return graph.compile()


def get_graph():
    global _COMPILED
    if _COMPILED is None:
        _COMPILED = build_graph()
    return _COMPILED


def apply_update(state: dict, update: dict) -> dict:
    """Same merge the graph uses: overwrite fields, append trace steps."""
    merged = dict(state)
    for key, value in update.items():
        if key == "trace":
            merged["trace"] = list(merged.get("trace") or []) + list(value)
        else:
            merged[key] = value
    return merged


def run_sequential(state: dict) -> dict:
    """Plain runner. Retrieval and data both read triage and do not read each other."""
    current = dict(state)
    current = apply_update(current, safety_node(current))
    current = apply_update(current, triage_node(current))
    retrieval_update = retrieval_node(current)
    data_update = data_node(current)
    current = apply_update(current, retrieval_update)
    current = apply_update(current, data_update)
    current = apply_update(current, escalation_node(current))
    current = apply_update(current, composer_node(current))
    return current


def run_turn(
    text: str,
    persona: str | None = None,
    request_id: str | None = None,
) -> tuple[CopilotResponse, list[dict]]:
    state = {
        "request_id": request_id or uuid.uuid4().hex[:8],
        "persona": persona or "",
        "raw_text": text,
        "masked_text": "",
        "trace": [],
    }
    final = get_graph().invoke(state)
    CopilotState.model_validate(final)
    response = CopilotResponse.model_validate(final["response"])
    return response, list(final.get("trace") or [])


def run_copilot(text: str, persona: str | None = None, request_id: str | None = None) -> CopilotResponse:
    response, _trace = run_turn(text, persona=persona, request_id=request_id)
    return response
