"""Root cause agent: turns retrieved precedents into ranked, confidence-scored
hypotheses.

Confidence is derived from retrieval similarity scores on past-incident documents
specifically (not runbooks; a runbook describes a pattern, an incident confirms one
actually happened that way before). If confidence on the best hypothesis is too low,
the agent signals the supervisor to retry retrieval with a broadened query rather than
forcing a low-confidence answer through.
"""

from __future__ import annotations

from ..llm import get_llm_client
from ..state import IncidentState, RootCauseHypothesis

LOW_CONFIDENCE_THRESHOLD = 0.15
MAX_RETRIEVAL_RETRIES = 2


def root_cause_node(state: IncidentState) -> IncidentState:
    retrieved = state.get("retrieved", [])
    incidents = [d for d in retrieved if d["doc_type"] == "incident"]

    hypotheses: list[RootCauseHypothesis] = []
    if incidents:
        total_score = sum(d["score"] for d in incidents) or 1.0
        for doc in incidents:
            hypotheses.append(
                RootCauseHypothesis(
                    hypothesis=f"Pattern matches precedent {doc['doc_id']}: {doc['title']}",
                    confidence=round(doc["score"] / total_score, 2),
                )
            )
    hypotheses.sort(key=lambda h: h["confidence"], reverse=True)

    llm = get_llm_client()
    llm.generate(
        system_prompt=(
            "You are an SRE root-cause analyst. Given matched precedent incidents, "
            "explain in 1-2 sentences why they're relevant to the current signal."
        ),
        user_prompt=str(incidents),
    )

    top_confidence = hypotheses[0]["confidence"] if hypotheses else 0.0
    iterations = state.get("iterations", 0)

    if top_confidence < LOW_CONFIDENCE_THRESHOLD and iterations < MAX_RETRIEVAL_RETRIES:
        next_step = "retrieval"
    else:
        next_step = "runbook_recommender"

    return {
        **state,
        "hypotheses": hypotheses,
        "next_step": next_step,
    }
