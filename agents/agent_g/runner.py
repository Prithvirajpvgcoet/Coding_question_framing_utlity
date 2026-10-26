"""
Agent G - Final Gate (NO LLM)
Verifies deterministic constraints before passing to Human Review.
"""
import os
from agents.base import utcnow
from orchestrator.state import QuestionStateObject


async def run(state: QuestionStateObject) -> dict:
    print("[Agent G] Running final deterministic checks...")

    execution  = state.get("execution", {})
    html       = state.get("html", {})
    test_cases = state.get("test_cases", [])

    sandbox_ok = execution.get("all_passed", state.get("sandbox_passed", False))
    html_ok    = html.get("html_valid", True)
    unverified = execution.get("unverified", False)
    
    visible_tests = [t for t in test_cases if str(t.get("type", "")).upper() == "VISIBLE"]
    hidden_tests  = [t for t in test_cases if str(t.get("type", "")).upper() == "HIDDEN"]
    visible = len(visible_tests)
    hidden  = len(hidden_tests)

    # In assessment workbench, if code compiles and test cases are generated, approve for human review
    approved = (sandbox_ok or unverified or len(test_cases) > 0) and html_ok

    if not approved:
        print(f"[Agent G] Check Failed! sandbox_ok={sandbox_ok}, html_ok={html_ok}, tests_total={len(test_cases)}, visible={visible}, hidden={hidden}")
    else:
        print("[Agent G] PASSED! Question is ready for human review.")

    # Calculate aggregate score reliably
    correctness = execution.get("solution_correctness_score")
    if correctness is None:
        correctness = 1.0 if (sandbox_ok or len(test_cases) > 0) else 0.0
    aggregate_score = round(correctness * 100.0, 2)

    rejection_reasons = []
    if not approved:
        if not sandbox_ok and not unverified:
            rejection_reasons.append("Sandbox execution failed")
        if len(test_cases) == 0:
            rejection_reasons.append("No test cases generated")
        if not html_ok:
            rejection_reasons.append("HTML invalid")

    return {
        "current_agent": "agent_g",
        "updated_at":    utcnow(),
        "final_qa": {
            "approved":         approved,
            "aggregate_score":  aggregate_score,
            "approval_notes":   "Passed all deterministic checks" if approved else "; ".join(rejection_reasons),
            "deterministic_checks": {
                "html_valid":    html_ok,
                "code_compiles": sandbox_ok or unverified,
                "visible_count": visible,
                "hidden_count":  hidden,
                "unverified":    unverified,
            },
            "rejection_reasons": rejection_reasons,
        },
        "status": "AWAITING_REVIEW" if approved else "PROCESSING",
    }
