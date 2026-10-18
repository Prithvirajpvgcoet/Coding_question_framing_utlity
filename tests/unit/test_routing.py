"""
Unit tests for LangGraph conditional edge routing functions.
Verifies fixes for P0.1, P0.2, P0.3, and Agent G routing.
"""
import pytest
from orchestrator import edges


def test_agent_d_pass_routes_to_agent_g(sample_state):
    """When Agent D quality passes and consistency is OK, route to Agent G."""
    state = {
        **sample_state,
        "quality": {"pass": True, "scores": {"clarity": 5.0}, "avg_score": 4.5},
        "consistency": {"consistent": True, "mismatches": []},
        "retry_counts": {"agent_c_external": 0},
    }
    assert edges.route_after_agent_d(state) == "agent_g"


def test_agent_d_fail_routes_to_agent_c(sample_state):
    """When Agent D quality fails and retry count is under limit, retry Agent C."""
    state = {
        **sample_state,
        "quality": {"pass": False, "scores": {"clarity": 2.0}, "avg_score": 2.5},
        "consistency": {"consistent": True, "mismatches": []},
        "retry_counts": {"agent_c_external": 1},
    }
    assert edges.route_after_agent_d(state) == "agent_c"


def test_agent_d_max_retries_escalates_to_human(sample_state):
    """When Agent D quality fails and retry limit reached, escalate to human."""
    state = {
        **sample_state,
        "quality": {"pass": False, "scores": {}, "avg_score": 2.0},
        "consistency": {"consistent": True, "mismatches": []},
        "retry_counts": {"agent_c_external": 3},
    }
    assert edges.route_after_agent_d(state) == "human_escalation"


def test_agent_f_requirements_routes_to_agent_a(sample_state):
    """Agent F revision route 'agent_a' correctly routes to Agent A."""
    state = {
        **sample_state,
        "revision_route": "agent_a",
    }
    assert edges.route_after_agent_f(state) == "agent_a"


def test_agent_f_logic_routes_to_agent_c(sample_state):
    """Agent F revision route 'agent_c' correctly routes to Agent C."""
    state = {
        **sample_state,
        "revision_route": "agent_c",
    }
    assert edges.route_after_agent_f(state) == "agent_c"


def test_agent_f_formatting_routes_to_agent_d(sample_state):
    """Agent F revision route 'agent_d' correctly routes to Agent D."""
    state = {
        **sample_state,
        "revision_route": "agent_d",
    }
    assert edges.route_after_agent_f(state) == "agent_d"


def test_route_after_dedup_pass_routes_to_agent_d(sample_state):
    """Dedup node after Agent C: PASS routes to Agent D for quality evaluation."""
    state = {
        **sample_state,
        "deduplication": {"verdict": "PASS", "similarity_score": 0.1},
    }
    assert edges.route_after_dedup(state) == "agent_d"


def test_route_after_dedup_reject_routes_to_agent_a(sample_state):
    """Dedup node after Agent C: REJECT routes back to Agent A for a new blueprint."""
    state = {
        **sample_state,
        "deduplication": {"verdict": "REJECT", "similarity_score": 0.95},
    }
    assert edges.route_after_dedup(state) == "agent_a"


def test_route_after_agent_g_approved(sample_state):
    """When Agent G final QA approves, end the graph (__end__)."""
    state = {
        **sample_state,
        "final_qa": {"approved": True, "aggregate_score": 95.0},
        "retry_counts": {"agent_c_external": 0},
    }
    assert edges.route_after_agent_g(state) == "__end__"


def test_route_after_agent_g_rejected_retries_agent_c(sample_state):
    """When Agent G rejects and retries available, retry Agent C."""
    state = {
        **sample_state,
        "final_qa": {"approved": False, "rejection_reasons": ["sandbox fail"]},
        "retry_counts": {"agent_c_external": 0},
    }
    assert edges.route_after_agent_g(state) == "agent_c"


def test_route_after_agent_g_rejected_max_retries_escalates(sample_state):
    """When Agent G rejects and retries exhausted, escalate to human."""
    state = {
        **sample_state,
        "final_qa": {"approved": False, "rejection_reasons": ["sandbox fail"]},
        "retry_counts": {"agent_c_external": 3},
    }
    assert edges.route_after_agent_g(state) == "human_escalation"
