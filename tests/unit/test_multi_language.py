"""
Unit tests for multi-language handling, sandbox verification, and timeout isolation.
Verifies P1.4 and P2.1/P2.2.
"""
import pytest
from services.client_config import get_language_tier, LANGUAGE_TIERS
from agents.agent_c.sandbox_exec import execute_and_verify
from services.sandbox_client import run_in_sandbox


def test_language_tier_classification():
    """Verify classification of T1, T2, T3 languages."""
    assert get_language_tier("python") == "T1"
    assert get_language_tier("java") == "T1"
    assert get_language_tier("javascript") == "T1"
    assert get_language_tier("cpp") == "T1"

    assert get_language_tier("typescript") == "T2"
    assert get_language_tier("ruby") == "T2"
    assert get_language_tier("kotlin") == "T2"

    assert get_language_tier("sql") == "T3"
    assert get_language_tier("html") == "T3"
    assert get_language_tier("react") == "T3"


@pytest.mark.asyncio
async def test_non_python_marked_unverified_and_fails_passed():
    """Non-Python code must not silently pass — must return passed=False and unverified=True."""
    java_code = "public class Solution { public int solve() { return 42; } }"
    result = await execute_and_verify(java_code, "java", [])
    assert result["passed"] is False
    assert result["unverified"] is True
    assert "[UNVERIFIED]" in result.get("output", "")


@pytest.mark.asyncio
async def test_python_language_neutral_test_cases():
    """Python code tested against language-neutral test case structure."""
    py_code = """
def solution(a, b):
    return a + b
"""
    # Language-neutral inputs/expected format
    test_cases = [
        {"type": "VISIBLE", "inputs": {"a": 2, "b": 3}, "expected": 5},
        {"type": "HIDDEN", "inputs": {"a": -1, "b": 1}, "expected": 0},
    ]
    result = await execute_and_verify(py_code, "python", test_cases)
    assert result["passed"] is True
    assert "All tests passed!" in result["output"]


@pytest.mark.asyncio
async def test_sandbox_timeout_kills_process():
    """Infinite loop in Python code must be terminated by sandbox timeout."""
    infinite_loop_code = """
while True:
    pass
"""
    result = await run_in_sandbox(infinite_loop_code, "python")
    assert result["passed"] is False
    assert "Timeout" in result.get("output", "")
