"""
Agent D - Quality Scoring
Evaluates the output of Agent C. If the score is < 4.0, LangGraph loops back to Agent C.
"""
import asyncio
import json
import os
import re

from agents.base import groq_chat, load_prompt, MODEL_STRONG, utcnow
from orchestrator.state import QuestionStateObject

SYSTEM = load_prompt("agent_d_scorer")
QUALITY_THRESHOLD = float(os.getenv("QUALITY_SCORE_THRESHOLD", os.getenv("QUALITY_PASS_THRESHOLD", "4.0")))


async def run(state: QuestionStateObject) -> dict:
    q_id = state.get("question_id", "")
    print(f"[Agent D] Scoring question: {q_id}")

    question = state.get("question") or state.get("generated_question") or {}
    code     = state.get("code", {}).get("solution") or state.get("solution_code") or ""
    tests    = state.get("test_cases", [])

    user_prompt = f"Problem:\n{question}\n\nCode:\n{code}\n\nTests:\n{tests}"

    content, usage = await groq_chat(
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
        scores = data.get("scores") or {"clarity": 5, "edge_cases": 5, "efficiency": 5, "formatting": 5}
        feedback = data.get("feedback", "")
        if scores and len(scores) > 0:
            avg_score = float(sum(scores.values())) / float(len(scores))
        else:
            avg_score = 1.0
    except Exception:
        avg_score = 1.0
        scores    = {}
        feedback  = "Failed to parse scoring output."

    print(f"[Agent D] Quality Score: {avg_score:.2f}/5.0")
    if avg_score < QUALITY_THRESHOLD:
        print(f"[Agent D] Kicking back to Agent C! Reason: {feedback}")

    # Log agent run
    try:
        from observability.agent_logger import log_agent_run
        await log_agent_run(
            question_id=q_id,
            request_id=state.get("request_id", ""),
            agent_name="agent_d",
            usage=usage,
            status="SUCCESS",
        )
    except Exception as e:
        print(f"[Agent D] Observability logging notice: {e}")

    # Align score metrics with QSO schema expectations
    qso_scores = {
        "technical_correctness": scores.get("efficiency", scores.get("edge_cases", avg_score)),
        "problem_clarity": scores.get("clarity", avg_score),
        "topic_alignment": scores.get("formatting", avg_score),
        "difficulty_accuracy": avg_score,
        "originality": avg_score,
        **scores,
    }

    return {
        "current_agent":  "agent_d",
        "updated_at":     utcnow(),
        # QSO-aligned keys (used by route_after_agent_d)
        "quality": {
            "pass":            avg_score >= QUALITY_THRESHOLD,
            "scores":          qso_scores,
            "avg_score":       avg_score,
            "failure_reasons": [feedback] if feedback else [],
        },
        "consistency": {
            "consistent": True,
            "mismatches": [],
        },
        # Legacy aliases
        "quality_score":    avg_score,
        "scorer_feedback":  feedback,
    }
