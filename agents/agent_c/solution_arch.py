import json
import re
from agents.base import groq_chat, load_prompt, MODEL_STRONG

SYSTEM = load_prompt("agent_c_solution_arch")

async def design_solution(question: dict, blueprint: dict) -> dict:
    user_prompt = f"Problem:\n{question.get('description_markdown')}\n\nConstraints: {blueprint.get('constraints')}"
    content, _ = await groq_chat(
        model=MODEL_STRONG,
        system=SYSTEM,
        user=user_prompt,
        agent_name="agent_c.solution_arch",
        json_mode=True
    )
    text = re.sub(r"^```(?:json)?\s*", "", content.strip())
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        return {"algorithm": "fallback", "time_complexity": "O(1)", "space_complexity": "O(1)", "edge_cases": []}