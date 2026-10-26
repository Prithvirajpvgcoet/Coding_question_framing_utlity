import json
import re
from agents.base import groq_chat, load_prompt, MODEL_CHEAP

SYSTEM = load_prompt("agent_c_html_format")

def _clean_json(text: str) -> str:
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
    return cleaned.strip()

async def format_html(markdown_or_html: str) -> str:
    """
    Returns platform-standard HTML for the question description.
    If the content already contains platform tags (<em><strong>, <!--[if-->, #eeeeee),
    preserves it directly to maintain exact formatting fidelity.
    """
    if not markdown_or_html:
        return "<p>No description provided.</p>"

    # If it is already formatted with the platform template, return directly
    if "<!--[if-->" in markdown_or_html and "#eeeeee" in markdown_or_html:
        return markdown_or_html

    user_prompt = f"""Convert this problem description into official assessment platform HTML format:
{markdown_or_html}

Return JSON: {{"html": "<formatted html>"}}
"""

    content, _ = await groq_chat(
        model=MODEL_CHEAP,
        system=SYSTEM,
        user=user_prompt,
        agent_name="agent_c.html_format",
        temperature=0.1,
        json_mode=True
    )
    
    try:
        data = json.loads(_clean_json(content))
        html_content = data.get("html")
        if html_content and len(html_content.strip()) > 0:
            return html_content
    except Exception:
        pass
        
    paragraphs = [f"<p>{p.strip()}</p>" for p in markdown_or_html.split("\n\n") if p.strip()]
    return "".join(paragraphs) if paragraphs else f"<p>{markdown_or_html}</p>"
