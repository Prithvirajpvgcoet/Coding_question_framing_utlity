"""
Agent G - Final Gate (NO LLM)
Verifies deterministic constraints before passing to Human Review.
"""
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
    visible    = len([t for t in test_cases if t.get("type") == "VISIBLE"])
    hidden     = len([t for t in test_cases if t.get("type") == "HIDDEN"])

    # Pass if: sandbox passed (or unverified/non-python), HTML valid, at least some tests
    approved = (sandbox_ok or unverified) and html_ok and (visible + hidden) > 0

    if not approved:
        print("[Agent G] Check Failed! Missing tests or sandbox failed.")
    else:
        print("[Agent G] PASSED! Question is ready for human review.")

    return {
        "current_agent": "agent_g",
        "updated_at":    utcnow(),
        "final_qa": {
            "approved":         approved,
            "aggregate_score":  execution.get("solution_correctness_score", 0.0) * 100,
            "deterministic_checks": {
                "html_valid":    html_ok,
                "code_compiles": sandbox_ok,
                "visible_count": visible,
                "hidden_count":  hidden,
                "unverified":    unverified,
            },
            "rejection_reasons": [] if approved else [
                "Sandbox failed or missing tests" if not sandbox_ok and not unverified
                else "No test cases generated" if (visible + hidden) == 0
                else "HTML invalid"
            ],
        },
        "status": "AWAITING_REVIEW" if approved else "PROCESSING",
    }
