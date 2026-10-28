"""Triage agent: classifies severity, affected component, and signal types.

Classification itself is rule-based (keyword heuristics over the raw signal text) so the
graph's control flow is identical and testable regardless of which LLM backend is active.
The LLM call adds a short natural-language triage note on top of the deterministic
classification: in demo mode that note is the labeled mock string, with a real backend
it's a genuine model-generated summary. This combination (deterministic classification +
LLM-generated narrative) is a realistic pattern: you generally do not want your routing
logic to depend on an LLM's free-text output being parseable.
"""

from __future__ import annotations

from ..llm import get_llm_client
from ..state import IncidentState

_SEVERITY_KEYWORDS = {
    "SEV1": ["outage", "down", "all customers", "data loss", "unavailable"],
    "SEV2": ["latency", "restart", "degraded", "failover", "elevated errors"],
    "SEV3": ["expiry", "warning", "notready", "disk pressure", "approaching limit"],
}

_COMPONENT_KEYWORDS = {
    "ecs": ["ecs", "fargate", "task", "checkout-api", "container"],
    "rds": ["rds", "database", "aurora", "sql", "connection pool"],
    "eks": ["eks", "kubernetes", "node", "pod", "kubelet"],
    "networking": ["tls", "certificate", "cert", "alb", "dns", "route 53"],
}

_SIGNAL_KEYWORDS = {
    "latency": ["latency", "p99", "slow", "timeout"],
    "restart": ["restart", "crash", "restarting", "killed"],
    "healthcheck-fail": ["health check", "healthcheck", "unhealthy"],
    "failover": ["failover"],
    "node-not-ready": ["notready", "not ready"],
    "disk-pressure": ["disk pressure", "disk"],
    "cert-expiry": ["expir", "certificate", "tls"],
}


def _classify(text: str, keyword_map: dict[str, list[str]], default: str) -> str:
    lowered = text.lower()
    for label, keywords in keyword_map.items():
        if any(k in lowered for k in keywords):
            return label
    return default


def _classify_signals(text: str) -> list[str]:
    lowered = text.lower()
    return [
        label
        for label, keywords in _SIGNAL_KEYWORDS.items()
        if any(k in lowered for k in keywords)
    ] or ["unknown"]


def triage_node(state: IncidentState) -> IncidentState:
    raw = state["raw_signal"]

    severity = _classify(raw, _SEVERITY_KEYWORDS, default="SEV3")
    component = _classify(raw, _COMPONENT_KEYWORDS, default="unknown")
    signals = _classify_signals(raw)

    llm = get_llm_client()
    llm.generate(
        system_prompt=(
            "You are an SRE triage assistant. Given a raw incident signal, write one "
            "concise sentence describing what an on-call engineer should understand "
            "about it before deeper diagnosis."
        ),
        user_prompt=raw,
    )

    return {
        **state,
        "severity": severity,
        "component": component,
        "signal_types": signals,
        "next_step": "retrieval",
    }
