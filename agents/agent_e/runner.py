"""
Agent E - Feedback Classification
Only triggers when a human rejects a question via the frontend.
"""
import asyncio
import json
import re

from agents.base import groq_chat, load_prompt, MODEL_CHEAP, utcnow
from orchestrator.state import QuestionStateObject

SYSTEM = load_prompt("agent_e_feedback")


async def run(state: QuestionStateObject) -> dict:
    q_id = state.get("question_id", "")
    print(f"[Agent E] Classifying human feedback for: {q_id}")

    human_feedback = state.get("human_feedback", {})
    feedback_text  = human_feedback.get("feedback_text", str(human_feedback)) if isinstance(human_feedback, dict) else str(human_feedback)

    content, usage = await groq_chat(
        model=MODEL_CHEAP,
        system=SYSTEM,
        user=f"Human feedback: {feedback_text}",
        agent_name="agent_e",
        temperature=0.1,
        json_mode=True
    )

    text = re.sub(r"^```(?:json)?\s*", "", content.strip())
    text = re.sub(r"\s*```$", "", text)

    try:
        classification = json.loads(text)
    except Exception:
        classification = {"severity": "HIGH", "category": "LOGIC", "summary": feedback_text}

    print(f"[Agent E] Category: {classification.get('category')}")

    # Log agent run
    asyncio.ensure_future(__import__("observability.agent_logger", fromlist=["log_agent_run"]).log_agent_run(
        question_id=q_id,
        request_id=state.get("request_id", ""),
        agent_name="agent_e",
        usage=usage,
        status="SUCCESS",
    ))

    return {
        "current_agent":         "agent_e",
        "updated_at":            utcnow(),
        "feedback_classification": classification,
    }