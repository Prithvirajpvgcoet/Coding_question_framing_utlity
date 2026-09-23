import json
import re
from agents.base import groq_chat, load_prompt, MODEL_STRONG

SYSTEM = load_prompt("agent_c_test_case_gen")

async def generate_tests(question: dict) -> list:
    content, _ = await groq_chat(
        model=MODEL_STRONG,
        system=SYSTEM,
        user=question.get("description_markdown", "No description"),
        agent_name="agent_c.test_case_gen",
        json_mode=True
    )
    text = re.sub(r"^```(?:json)?\s*", "", content.strip())
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text).get("test_cases", [])
    except Exception:
        return []