import json
import re
from agents.base import groq_chat, load_prompt, MODEL_CODE

SYSTEM = load_prompt("agent_c_code_gen")

def _clean_json(text: str) -> str:
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
    return cleaned.strip()

async def generate(question: dict, architecture: dict, language: str, template: str) -> dict:
    function_name = question.get("function_name", "solution")
    user_prompt = f"""
Generate a COMPLETE working solution for this coding problem.

Language: {language}
Function name: {function_name}
Algorithm: {architecture.get('algorithm', '')}

Platform code template (fill in the logic):
```
{template}
```

Problem description:
{question.get('description_markdown', '')}

Rules:
1. Return the COMPLETE program including main() and I/O — not just the function body.
2. The function MUST be named exactly `{function_name}`.
3. Replace `result = -404` with the correct return value computation.
4. Keep all the existing I/O structure (stdin reading, stdout printing) intact.
5. Output a JSON object with key "code" containing the complete program.
"""
    content, _ = await groq_chat(
        model=MODEL_CODE,
        system=SYSTEM,
        user=user_prompt,
        agent_name="agent_c.code_gen",
        temperature=0.1,
        json_mode=True,
        max_tokens=800,
    )
    
    code = ""
    try:
        data = json.loads(_clean_json(content))
        code = data.get("code") or data.get("solution") or data.get("solution_code") or ""
    except Exception:
        # If model returned pure python without json structure
        cleaned = _clean_json(content)
        if "def " in cleaned:
            code = cleaned

    if not code:
        code = template if template else "def solution(*args, **kwargs):\n    return 0\n"
        
    return {"solution_code": code, "language": language}
