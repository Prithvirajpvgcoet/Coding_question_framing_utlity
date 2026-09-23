import json
import re
from agents.base import groq_chat, load_prompt, MODEL_CHEAP

SYSTEM = load_prompt("agent_c_html_format")

async def format_html(markdown: str) -> str:
    content, _ = await groq_chat(
        model=MODEL_CHEAP,
        system=SYSTEM,
        user=f"Markdown to convert:\n{markdown}",
        agent_name="agent_c.html_format",
        temperature=0.1,
        json_mode=True
    )
    text = re.sub(r"^```(?:json)?\s*", "", content.strip())
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text).get("html", markdown)
    except Exception:
        return markdown