"""
Agent E — Feedback Classification
Only triggers when a human rejects a question via the frontend.
"""
import json
import re
from agents.base import groq_chat, load_prompt, MODEL_CHEAP, utcnow
from orchestrator.state import QuestionStateObject

SYSTEM = load_prompt("agent_e_feedback")

async def run(state: QuestionStateObject) -> dict:
    print(f"[Agent E] Classifying human feedback for: {state.get('question_id')}")
    
    human_feedback = state.get("human_feedback", "")
    
    content, _ = await groq_chat(
        model=MODEL_CHEAP,
        system=SYSTEM,
        user=f"Human feedback: {human_feedback}",
        agent_name="agent_e",
        temperature=0.1,
        json_mode=True
    )
    
    text = re.sub(r"^```(?:json)?\s*", "", content.strip())
    text = re.sub(r"\s*```$", "", text)
    
    try:
        classification = json.loads(text)
    except Exception:
        classification = {"severity": "HIGH", "category": "LOGIC", "summary": human_feedback}

    print(f"[Agent E] Category: {classification.get('category')}")
    
    return {
        "current_agent": "agent_e",
        "updated_at": utcnow(),
        "feedback_classification": classification
    }