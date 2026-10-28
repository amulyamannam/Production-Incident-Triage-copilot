"""Shared state schema passed between nodes in the LangGraph graph.

Kept as a plain TypedDict (LangGraph's preferred shape) rather than a class with
methods, since every node only needs to read a few keys and write a few keys back.
"""

from __future__ import annotations

from typing import List, Optional, TypedDict


class RetrievedDoc(TypedDict):
    doc_id: str
    doc_type: str  # "runbook" | "incident"
    title: str
    score: float
    text: str


class RootCauseHypothesis(TypedDict):
    hypothesis: str
    confidence: float


class IncidentState(TypedDict, total=False):
    # input
    raw_signal: str

    # set by triage
    severity: str
    component: str
    signal_types: List[str]

    # set by retrieval
    retrieved: List[RetrievedDoc]

    # set by root_cause
    hypotheses: List[RootCauseHypothesis]

    # set by runbook_recommender
    recommended_runbook_id: Optional[str]
    recommended_action: str
    risk_note: str

    # control flow
    next_step: str
    iterations: int
