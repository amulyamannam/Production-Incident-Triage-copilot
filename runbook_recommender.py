"""Runbook recommender: maps the diagnosis to a concrete recommended action.

Pulls the "Recommended action" and "Anti-pattern to avoid" sections directly out of the
matched runbook markdown (deterministic, auditable) rather than asking the LLM to
freely restate them. For an operational recommendation, surfacing the actual runbook
text verbatim is safer than letting a model paraphrase it. The LLM call is used only to
produce a short framing sentence around it.
"""

from __future__ import annotations

import re

from ..llm import get_llm_client
from ..state import IncidentState


def _extract_section(markdown: str, heading: str) -> str:
    pattern = rf"## {re.escape(heading)}\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, markdown, re.DOTALL)
    return match.group(1).strip() if match else ""


def runbook_recommender_node(state: IncidentState) -> IncidentState:
    retrieved = state.get("retrieved", [])
    runbooks = sorted(
        (d for d in retrieved if d["doc_type"] == "runbook"),
        key=lambda d: d["score"],
        reverse=True,
    )

    llm = get_llm_client()

    if not runbooks:
        llm.generate(
            system_prompt="You are an SRE assistant.",
            user_prompt="No matching runbook was found for this incident.",
        )
        return {
            **state,
            "recommended_runbook_id": None,
            "recommended_action": (
                "No matching runbook found in the corpus. Escalate to a human on-call "
                "engineer for manual diagnosis rather than guessing."
            ),
            "risk_note": "Insufficient precedent to recommend an automated action.",
            "next_step": "done",
        }

    top = runbooks[0]
    action_text = _extract_section(top["text"], "Recommended action")
    risk_text = _extract_section(top["text"], "Anti-pattern to avoid")

    llm.generate(
        system_prompt=(
            "You are an SRE assistant. Write one short framing sentence introducing a "
            "recommended runbook action to an on-call engineer."
        ),
        user_prompt=f"Runbook: {top['title']}",
    )

    return {
        **state,
        "recommended_runbook_id": top["doc_id"],
        "recommended_action": action_text or "See full runbook for details.",
        "risk_note": risk_text or "No specific anti-pattern recorded for this runbook.",
        "next_step": "done",
    }
