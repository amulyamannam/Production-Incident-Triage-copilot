"""Supervisor: pure routing logic, no LLM call of its own.

Each worker node writes `next_step` into the state to declare what it thinks should
happen next (e.g. root_cause asking for another retrieval pass on low confidence). The
supervisor's job is just to read that and route, kept as a separate, trivial function
so the conditional-edge logic in `graph.py` stays easy to follow and unit-test.
"""

from __future__ import annotations

from ..state import IncidentState

VALID_STEPS = {"triage", "retrieval", "root_cause", "runbook_recommender", "done"}


def route(state: IncidentState) -> str:
    next_step = state.get("next_step", "triage")
    if next_step not in VALID_STEPS:
        return "done"
    return next_step
