"""
Agent F — Logic Router (NO LLM)
Reads Agent E's classification and sets the revision route.
"""
from agents.base import utcnow
from orchestrator.state import QuestionStateObject

async def run(state: QuestionStateObject) -> dict:
    print(f"[Agent F] Routing revision for: {state.get('question_id')}")
    
    classification = state.get("feedback_classification") or state.get("feedback_analysis", {})
    category = classification.get("category", "LOGIC")
    summary = classification.get("summary", "")
    
    blueprint = dict(state.get("blueprint", {}))
    
    # Route logic based on category
    if category == "REQUIREMENTS":
        route = "agent_a"
        blueprint["_revision_instruction"] = f"Human requested requirement change: {summary}"
    elif category == "FORMATTING":
        route = "agent_c"  # Formatting fixes must regenerate/reformat HTML in Agent C
        blueprint["previous_error"] = f"Human requested formatting fix: {summary}"
    else:
        route = "agent_c"  # Logic/code bugs go to C
        blueprint["previous_error"] = f"Human rejected: {summary}"

    print(f"[Agent F] Routing to: {route}")
    
    feedback_analysis = {
        "category": category,
        "summary": summary,
        "re_entry_agent": route,
        "severity": classification.get("severity", "MEDIUM"),
    }
    
    return {
        "current_agent": "agent_f",
        "updated_at": utcnow(),
        "revision_route": route,
        "feedback_analysis": feedback_analysis,
        "feedback_classification": feedback_analysis,
        "blueprint": blueprint
    }
