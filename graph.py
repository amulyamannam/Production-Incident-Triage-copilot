"""Wires the agent nodes into a LangGraph `StateGraph`.

Graph shape:

    triage -> retrieval -> root_cause --(low confidence, retries left)--> retrieval
                                       --(otherwise)--> runbook_recommender -> END

The conditional edge out of `root_cause` is the reason this is a graph and not a linear
chain: it's the one point where the system can decide it doesn't have enough evidence
and loop back, bounded by `MAX_RETRIEVAL_RETRIES` in `agents/root_cause.py` so it can't
loop forever.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from .agents.retriever_node import retrieval_node
from .agents.root_cause import root_cause_node
from .agents.runbook_recommender import runbook_recommender_node
from .agents.supervisor import route
from .agents.triage import triage_node
from .state import IncidentState


def build_graph():
    graph = StateGraph(IncidentState)

    graph.add_node("triage", triage_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("root_cause", root_cause_node)
    graph.add_node("runbook_recommender", runbook_recommender_node)

    graph.set_entry_point("triage")

    graph.add_edge("triage", "retrieval")

    graph.add_conditional_edges(
        "root_cause",
        route,
        {
            "retrieval": "retrieval",
            "runbook_recommender": "runbook_recommender",
            "done": END,
        },
    )
    graph.add_edge("retrieval", "root_cause")
    graph.add_edge("runbook_recommender", END)

    return graph.compile()


def run_incident(raw_signal: str) -> IncidentState:
    app = build_graph()
    initial_state: IncidentState = {"raw_signal": raw_signal, "iterations": 0}
    return app.invoke(initial_state)
