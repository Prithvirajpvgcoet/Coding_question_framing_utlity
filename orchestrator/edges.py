"""
Conditional edge routing functions for the 7-agent LangGraph graph.
Each function receives state and returns the name of the NEXT node.
"""
import os
from orchestrator.state import QuestionStateObject

MAX_EXTERNAL_RETRIES = int(os.getenv("MAX_EXTERNAL_RETRIES", 3))
MAX_REVISION_CYCLES  = int(os.getenv("MAX_REVISION_CYCLES", 5))
MAX_DEDUP_RETRIES    = int(os.getenv("MAX_DEDUP_RETRIES", 2))


def route_after_dedup(state: QuestionStateObject) -> str:
    """After deduplication check — REJECT goes back to Agent A (subject to budget), else proceed to Agent D."""
    verdict = state.get("deduplication", {}).get("verdict", "PASS")
    if verdict == "REJECT":
        retry_counts = state.get("retry_counts", {})
        dedup_retries = retry_counts.get("dedup_reject", 0)
        if dedup_retries >= MAX_DEDUP_RETRIES:
            print(f"[Edges] Dedup retry limit ({MAX_DEDUP_RETRIES}) reached. Escalating to human review.")
            return "human_escalation"
        
        # Increment dedup retry counter
        retry_counts["dedup_reject"] = dedup_retries + 1
        return "agent_a"          # Request a new blueprint/scenario
        
    return "agent_d"              # PASS or FLAG both proceed (FLAG = note in state)


def route_after_agent_d(state: QuestionStateObject) -> str:
    """After Agent D (Quality + Consistency) — fail retries Agent C, success goes to Agent G."""
    quality     = state.get("quality", {})
    consistency = state.get("consistency", {})

    all_passed = quality.get("pass", False) and consistency.get("consistent", True)

    if all_passed:
        return "agent_g"

    # Check retry budget
    retry_counts = state.get("retry_counts", {})
    retries = retry_counts.get("agent_c_external", 0)
    if retries >= MAX_EXTERNAL_RETRIES:
        return "human_escalation"

    retry_counts["agent_c_external"] = retries + 1
    return "agent_c"              # Retry Agent C with failure context


def route_after_agent_g(state: QuestionStateObject) -> str:
    """After Agent G (Final QA) — approved goes to END, else targeted fix."""
    fqa = state.get("final_qa", {})

    if fqa.get("approved", False):
        return "__end__"          # → status = AWAITING_REVIEW

    # Check retry budget
    retry_counts = state.get("retry_counts", {})
    retries = retry_counts.get("agent_c_external", 0)
    if retries >= MAX_EXTERNAL_RETRIES:
        return "human_escalation"

    retry_counts["agent_c_external"] = retries + 1

    checks = fqa.get("deterministic_checks", {})

    # Deterministic failures → targeted Agent C fix
    if not checks.get("html_valid", True):
        return "agent_c"
    if not checks.get("code_compiles", True):
        return "agent_c"
    if checks.get("visible_count", 0) < 1 or checks.get("hidden_count", 0) < 1:
        return "agent_c"

    # Score too low (percentage scale 0-100) → back to blueprint
    threshold = float(os.getenv("FINAL_QA_PERCENT_THRESHOLD", "70.0"))
    if fqa.get("aggregate_score", 0) < threshold:
        return "agent_a"

    return "human_escalation"


def route_after_agent_f(state: QuestionStateObject) -> str:
    """After Agent F (Revision Router) — route to A, C, or D based on feedback analysis."""
    target = state.get("revision_route")
    if not target:
        fa = state.get("feedback_analysis", {})
        target = fa.get("re_entry_agent", "agent_c")

    valid_targets = {"agent_a", "agent_c", "agent_d"}
    if target not in valid_targets:
        return "agent_c"          # Safe default

    return target
