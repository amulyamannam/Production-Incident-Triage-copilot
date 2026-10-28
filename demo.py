#!/usr/bin/env python
"""CLI entrypoint.

    python demo.py --incident "p99 latency on checkout-api jumped from 80ms to 4200ms, ECS tasks restarting"

Runs the full LangGraph agent graph against a single incident signal and prints the
triage, retrieval, root-cause, and recommendation results, clearly labeling whether the
LLM steps ran in DEMO_MODE or against a live backend.
"""

from __future__ import annotations

import argparse

from src.graph import run_incident
from src.llm import get_llm_client

DEFAULT_INCIDENT = (
    "p99 latency on checkout-api jumped from 80ms to 4200ms, ECS tasks restarting"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the agentic-infra-ops demo.")
    parser.add_argument(
        "--incident",
        default=DEFAULT_INCIDENT,
        help="Raw incident signal text to triage and diagnose.",
    )
    args = parser.parse_args()

    result = run_incident(args.incident)

    print(f"[triage]      severity={result['severity']}  "
          f"component={result['component']}  signal={'+'.join(result['signal_types'])}")

    retrieved = result.get("retrieved", [])
    runbooks = [d for d in retrieved if d["doc_type"] == "runbook"]
    incidents = [d for d in retrieved if d["doc_type"] == "incident"]
    print(f"[retrieval]   matched {len(runbooks)} runbooks, {len(incidents)} past incidents "
          f"(top score {max((d['score'] for d in retrieved), default=0):.2f})")

    print("[root_cause]  hypotheses:")
    for h in result.get("hypotheses", []):
        print(f"              ({h['confidence']:.2f}) {h['hypothesis']}")

    print("[runbook_recommender]")
    print(f"              Recommended runbook: {result.get('recommended_runbook_id')}")
    print(f"              Suggested next step: {result.get('recommended_action')}")
    print(f"              Risk note: {result.get('risk_note')}")

    client = get_llm_client()
    if client.demo_mode:
        print(
            "\n[DEMO MODE] No live LLM credentials detected, narrative LLM calls used "
            "deterministic demo output. See README 'Running with a real LLM backend'."
        )
    else:
        print(f"\n[LIVE] Reasoning steps used backend: {client.backend}")


if __name__ == "__main__":
    main()
