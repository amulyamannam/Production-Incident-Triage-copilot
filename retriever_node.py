"""Retrieval node: RAG lookup over the synthetic runbook + incident corpus.

Builds the retrieval query from the triage output (component + signal types) rather
than the raw free-text signal, since structured fields retrieve more precisely than the
original sentence once triage has already extracted them.
"""

from __future__ import annotations

from ..retrieval import get_retriever
from ..state import IncidentState


def retrieval_node(state: IncidentState) -> IncidentState:
    component = state.get("component", "")
    signals = " ".join(state.get("signal_types", []))
    query = f"{component} {signals} {state['raw_signal']}"

    retriever = get_retriever()
    results = retriever.search(query, top_k=4)

    iterations = state.get("iterations", 0) + 1

    return {
        **state,
        "retrieved": results,
        "iterations": iterations,
        "next_step": "root_cause",
    }
