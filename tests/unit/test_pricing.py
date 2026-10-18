"""
Unit tests for observability and cost computation.
Verifies fix for P1.3 (model key alignment and no fallback pricing for cheap models).
"""
import pytest
from observability.cost_tracker import compute_cost, COST_PER_1M
from agents.base import _compute_cost


def test_cheap_model_pricing_not_fallback():
    """Cheap tier openai/gpt-oss-20b must use $0.075 / $0.30 rates, not fallback."""
    # 1 million input tokens of openai/gpt-oss-20b should be $0.075
    cost_in = compute_cost("openai/gpt-oss-20b", 1_000_000, 0)
    assert pytest.approx(cost_in, rel=1e-4) == 0.075

    cost_out = compute_cost("openai/gpt-oss-20b", 0, 1_000_000)
    assert pytest.approx(cost_out, rel=1e-4) == 0.30

    # Ensure _compute_cost in base.py produces the exact same result
    base_cost = _compute_cost("openai/gpt-oss-20b", 1_000_000, 0)
    assert pytest.approx(base_cost, rel=1e-4) == 0.075


def test_code_model_pricing():
    """Code model qwen/qwen3.8-27b pricing must match $0.60 / $3.00."""
    cost = compute_cost("qwen/qwen3.8-27b", 1_000_000, 1_000_000)
    assert pytest.approx(cost, rel=1e-4) == 3.60


def test_strong_model_pricing():
    """Strong model openai/gpt-oss-120b pricing must match $0.59 / $0.79."""
    cost = compute_cost("openai/gpt-oss-120b", 1_000_000, 1_000_000)
    assert pytest.approx(cost, rel=1e-4) == 1.38
