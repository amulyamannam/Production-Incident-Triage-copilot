import os

os.environ["FORCE_DEMO_MODE"] = "true"

from src.graph import run_incident  # noqa: E402


def test_full_graph_runs_end_to_end():
    result = run_incident(
        "p99 latency on checkout-api jumped from 80ms to 4200ms, ECS tasks restarting"
    )
    assert result["severity"] in {"SEV1", "SEV2", "SEV3"}
    assert result["component"] == "ecs"
    assert "recommended_action" in result
    assert result.get("recommended_runbook_id") == "RB-014"


def test_graph_handles_unmatched_signal_gracefully():
    result = run_incident("zzqxv totally unrelated nonsense signal")
    # should not crash even with no good matches
    assert "recommended_action" in result
