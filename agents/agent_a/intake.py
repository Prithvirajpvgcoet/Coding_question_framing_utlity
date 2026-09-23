"""
Step 1: Extract structured requirements from raw client request.
Model: llama-3.1-8b-instant — fast + cheap for JSON extraction.
"""
import json
import re
from agents.base import groq_chat, load_prompt, MODEL_CHEAP

SYSTEM = load_prompt("agent_a_intake")


def _clean_json(text: str) -> str:
    """Strip markdown fences if model wraps output in ```json ... ```"""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


VALID_DIFFICULTIES = {"EASY", "MEDIUM", "HARD", "EXPERT"}
VALID_TYPES       = {"ALGORITHMIC", "SQL", "SYSTEM_DESIGN", "DEBUG", "FILL_IN_BLANK"}
VALID_LANGUAGES   = {"python", "javascript", "java", "cpp", "go", "typescript"}


async def extract_requirements(raw_request: str) -> dict:
    """
    Call llama-3.1-8b-instant to extract structured requirements.
    Falls back to sensible defaults on any parse error.
    """
    content, usage = await groq_chat(
        model=MODEL_CHEAP,
        system=SYSTEM,
        user=f"Client request: {raw_request}",
        agent_name="agent_a.intake",
        temperature=0.1,
        json_mode=True,
    )

    try:
        data = json.loads(_clean_json(content))
    except (json.JSONDecodeError, ValueError):
        data = {}

    # Sanitize and apply defaults
    return {
        "topic":                  str(data.get("topic",    "Arrays")).strip(),
        "subtopic":               str(data.get("subtopic", "")).strip(),
        "difficulty":             data.get("difficulty", "MEDIUM").upper()
                                      if data.get("difficulty", "").upper() in VALID_DIFFICULTIES
                                      else "MEDIUM",
        "question_type":          data.get("question_type", "ALGORITHMIC").upper()
                                      if data.get("question_type", "").upper() in VALID_TYPES
                                      else "ALGORITHMIC",
        "target_language":        data.get("target_language", "python").lower()
                                      if data.get("target_language", "").lower() in VALID_LANGUAGES
                                      else "python",
        "max_solve_time_minutes": int(data.get("max_solve_time_minutes", 30)),
        "custom_constraints":     list(data.get("custom_constraints", [])),
        "raw_request":            raw_request,
        "_intake_usage":          usage,
    }