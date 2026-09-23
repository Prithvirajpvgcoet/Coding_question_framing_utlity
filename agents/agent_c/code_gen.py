import json
import re
from agents.base import groq_chat, load_prompt, MODEL_CODE

SYSTEM = load_prompt("agent_c_code_gen")

async def generate(question: dict, architecture: dict, language: str, template: str) -> dict:
    user_prompt = f"""
    Language: {language}
    Template: {template}
    Algorithm: {architecture.get('algorithm')}
    Problem: {question.get('description_markdown')}
    """
    content, _ = await groq_chat(
        model=MODEL_CODE,   # Using the Qwen Coder model here!
        system=SYSTEM,
        user=user_prompt,
        agent_name="agent_c.code_gen",
        temperature=0.1,
        json_mode=True
    )
    text = re.sub(r"^```(?:json)?\s*", "", content.strip())
    text = re.sub(r"\s*```$", "", text)
    try:
        code = json.loads(text).get("code", "pass")
    except Exception:
        code = "pass"
        
    return {"solution_code": code, "language": language}