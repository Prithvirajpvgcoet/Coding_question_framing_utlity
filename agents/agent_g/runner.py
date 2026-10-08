"""
Agent G — Final Gate (NO LLM)
Verifies deterministic constraints before passing to Human Review.
"""
from agents.base import utcnow
from orchestrator.state import QuestionStateObject

async def run(state: QuestionStateObject) -> dict:
    print(f"[Agent G] Running final deterministic checks...")
    
    sandbox_passed = state.get("sandbox_passed", False)
    test_cases = state.get("test_cases", [])
    
    # Check 1: Must have passed sandbox
    # Check 2: Must have generated test cases
    fail = False
    if not sandbox_passed or len(test_cases) == 0:
        fail = True
        print("[Agent G] Check Failed! Missing tests or sandbox failed.")

    # Update final status
    status = "PROCESSING" if fail else "AWAITING_REVIEW"
    
    if not fail:
        print("[Agent G] ✅ PASSED! Question is ready for human review.")
        
    return {
        "current_agent": "agent_g",
        "updated_at": utcnow(),
        "deterministic_fail": fail,
        "status": status
    }
