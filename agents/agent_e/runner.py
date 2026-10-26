"""
Agent E — Human Review & Feedback Intake
Classifies human review comments to determine revision strategy.
No state changes except feedback_classification / feedback_analysis.
"""
import asyncio
import json
import re
from agents.base import groq_chat, MODEL_FAST, utcnow
from orchestrator.state import QuestionStateObject

SYSTEM = """You are a senior technical reviewer.
Analyze the human feedback on a coding assessment question and classify it.
Output ONLY valid JSON matching this schema:
{
  "category": "REQUIREMENTS" | "LOGIC" | "FORMATTING" | "DIFFICULTY" | "TEST_CASES",
  "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "summary": "1-2 sentence technical summary of what needs fixing",
  "suggested_fix": "Specific instruction for the fixing agent"
}
Return ONLY a valid JSON object.
"""

def _clean_json(text: str) -> str:
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
    return cleaned.strip()

async def run(state: QuestionStateObject) -> dict:
    q_id = state.get("question_id", "unknown")
    print(f"[Agent E] Ingesting feedback for: {q_id}")

    human_feedback = state.get("human_feedback", {})
    feedback_text = human_feedback.get("feedback_text", "")

    if not feedback_text:
        classification = {
            "category": "LOGIC",
            "severity": "LOW",
            "summary": "No specific feedback provided.",
            "suggested_fix": "Verify code against all constraints.",
        }
        usage = {}
    else:
        user_prompt = f"Human feedback: {feedback_text}"
        text, usage = await groq_chat(
            model=MODEL_FAST,
            system=SYSTEM,
            user=user_prompt,
            agent_name="agent_e",
            json_mode=True,
        )

        try:
            classification = json.loads(_clean_json(text))
        except Exception:
            classification = {"severity": "HIGH", "category": "LOGIC", "summary": feedback_text, "suggested_fix": "Review logic"}

    print(f"[Agent E] Category: {classification.get('category')}")

    # Use asyncio task/ensure_future for non-blocking logging
    try:
        from observability.agent_logger import log_agent_run
        asyncio.ensure_future(log_agent_run(
            question_id=q_id,
            request_id=state.get("request_id", ""),
            agent_name="agent_e",
            usage=usage,
            status="SUCCESS",
        ))
    except Exception as e:
        print(f"[Agent E] Observability logging notice: {e}")

    return {
        "current_agent": "agent_e",
        "updated_at": utcnow(),
        "feedback_classification": classification,
        "feedback_analysis": classification,
    }
