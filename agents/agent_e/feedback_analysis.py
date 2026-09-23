"""
Classify feedback + determine re-entry agent.
Model: llama-3.1-8b-instant — cheap + fast for simple classification.
"""
from agents.base import MODEL_CHEAP, load_prompt

SYSTEM = load_prompt("agent_e_feedback")

COMPONENT_TO_AGENT = {
    "difficulty":  "agent_a",
    "scope":       "agent_a",
    "scenario":    "agent_a",
    "question":    "agent_c",
    "clarity":     "agent_c",
    "wording":     "agent_c",
    "html":        "agent_c",
    "code":        "agent_c",
    "tests":       "agent_c",
    "consistency": "agent_d",
    "quality":     "agent_d",
}


async def analyze(feedback_text: str, state: dict) -> dict:
    """
    Phase 6+: Replace stub with:
        content, usage = await groq_chat(
            model=MODEL_CHEAP,
            system=SYSTEM,
            user=f"Feedback: {feedback_text}",
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        result = json.loads(content)
        result["re_entry_agent"] = COMPONENT_TO_AGENT.get(
            result.get("primary_component", "question"), "agent_c"
        )
        return result
    """
    return {}   # Phase 0 stub