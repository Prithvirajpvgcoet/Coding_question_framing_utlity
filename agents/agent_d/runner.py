"""
Agent D — Quality Scoring
Evaluates the output of Agent C. If the score is < 4.0, LangGraph loops back to Agent C!
"""
import json
import os
import re
from agents.base import groq_chat, load_prompt, MODEL_STRONG, utcnow
from orchestrator.state import QuestionStateObject

SYSTEM = load_prompt("agent_d_scorer")

async def run(state: QuestionStateObject) -> dict:
    print(f"[Agent D] Scoring question: {state.get('question_id')}")
    
    question = state.get("generated_question", {})
    code = state.get("solution_code", "")
    tests = state.get("test_cases", [])
    
    user_prompt = f"Problem:\n{question}\n\nCode:\n{code}\n\nTests:\n{tests}"
    
    content, _ = await groq_chat(
        model=MODEL_STRONG,
        system=SYSTEM,
        user=user_prompt,
        agent_name="agent_d",
        json_mode=True
    )
    
    text = re.sub(r"^```(?:json)?\s*", "", content.strip())
    text = re.sub(r"\s*```$", "", text)
    
    try:
        data = json.loads(text)
        scores = data.get("scores", {"clarity": 5, "edge_cases": 5, "efficiency": 5, "formatting": 5})
        feedback = data.get("feedback", "")
        avg_score = sum(scores.values()) / len(scores)
    except Exception:
        avg_score = 1.0  # Force fail on parse error
        feedback = "Failed to parse scoring output."

    print(f"[Agent D] Quality Score: {avg_score}/5.0")
    if avg_score < 4.0:
        print(f"[Agent D] Kicking back to Agent C! Reason: {feedback}")
        
    return {
        "current_agent": "agent_d",
        "updated_at": utcnow(),
        "quality_score": avg_score,
        "scorer_feedback": feedback
    }
