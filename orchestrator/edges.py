"""
Conditional edge routing functions for the 7-agent LangGraph graph.
Each function receives state and returns the name of the NEXT node.
"""
import os
from orchestrator.state import QuestionStateObject

MAX_EXTERNAL_RETRIES = int(os.getenv("MAX_EXTERNAL_RETRIES", 3))
MAX_REVISION_CYCLES  = int(os.getenv("MAX_REVISION_CYCLES", 5))


def route_after_dedup(state: QuestionStateObject) -> str:
    """After deduplication check — REJECT goes back to Agent A, else proceed to Agent C."""
    verdict = state.get("deduplication", {}).get("verdict", "PASS")
    if verdict == "REJECT":
        return "agent_a"          # Request a new blueprint/scenario
    return "agent_c"              # PASS or FLAG both proceed (FLAG = note in state)


def route_after_agent_d(state: QuestionStateObject) -> str:
    """After Agent D (Quality + Consistency) — fail retries Agent C, success goes to Agent G."""
    quality     = state.get("quality", {})
    consistency = state.get("consistency", {})

    all_passed = quality.get("pass", False) and consistency.get("consistent", True)

    if all_passed:
        return "agent_g"

    # Check retry budget
    retries = state.get("retry_counts", {}).get("agent_c_external", 0)
    if retries >= MAX_EXTERNAL_RETRIES:
        return "human_escalation"

    return "agent_c"              # Retry Agent C with failure context


def route_after_agent_g(state: QuestionStateObject) -> str:
    """After Agent G (Final QA) — approved goes to END, else targeted fix."""
    fqa = state.get("final_qa", {})

    if fqa.get("approved", False):
        return "__end__"          # → status = AWAITING_REVIEW

    checks = fqa.get("deterministic_checks", {})

    # Deterministic failures → targeted Agent C fix
    if not checks.get("html_valid", True):
        return "agent_c"
    if not checks.get("code_compiles", True):
        return "agent_c"
    if checks.get("visible_count", 0) < 3 or checks.get("hidden_count", 0) < 3:
        return "agent_c"

    # Score too low → back to blueprint
    if fqa.get("aggregate_score", 0) < float(os.getenv("QUALITY_PASS_THRESHOLD", 70)):
        return "agent_a"

    return "human_escalation"


def route_after_agent_f(state: QuestionStateObject) -> str:
    """After Agent F (Revision Router) — route to A, C, or D based on feedback analysis."""
    fa = state.get("feedback_analysis", {})
    target = fa.get("re_entry_agent", "agent_c")

    valid_targets = {"agent_a", "agent_c", "agent_d"}
    if target not in valid_targets:
        return "agent_c"          # Safe default

    return target