import json
import re
from typing import Optional, List, Dict, Any
from agents.base import groq_chat, load_prompt, MODEL_STRONG

SYSTEM = load_prompt("agent_c_question_gen")

async def generate(blueprint: dict, references: Optional[List[Dict[str, Any]]] = None) -> dict:
    prompt_payload = {
        "blueprint": blueprint,
    }
    if references:
        prompt_payload["domain_references"] = references

    content, usage = await groq_chat(
        model=MODEL_STRONG,
        system=SYSTEM,
        user=json.dumps(prompt_payload),
        agent_name="agent_c.question_gen",
        json_mode=True
    )
    # Basic cleanup
    text = re.sub(r"^```(?:json)?\s*", "", content.strip())
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        return {"title": "Error", "description_markdown": "Fallback content", "examples": [], "constraints_list": []}