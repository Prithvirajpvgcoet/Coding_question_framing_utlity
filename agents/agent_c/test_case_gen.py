import json
import re
from agents.base import groq_chat, load_prompt, MODEL_STRONG

SYSTEM = load_prompt("agent_c_test_case_gen")

def _clean_json(text: str) -> str:
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
    return cleaned.strip()

async def generate_tests(question: dict) -> list:
    content, _ = await groq_chat(
        model=MODEL_STRONG,
        system=SYSTEM,
        user=f"Problem description:\n{question.get('description_markdown', 'Solve the problem.')}\n\nReturn JSON with test_cases list containing VISIBLE and HIDDEN test cases.",
        agent_name="agent_c.test_case_gen",
        json_mode=True
    )
    
    try:
        data = json.loads(_clean_json(content))
        test_cases = data.get("test_cases", [])
        if isinstance(test_cases, list) and len(test_cases) > 0:
            # Normalize casing for test types
            for tc in test_cases:
                t = str(tc.get("type", "VISIBLE")).upper()
                tc["type"] = "HIDDEN" if "HIDDEN" in t else "VISIBLE"
            return test_cases
    except Exception:
        pass

    # Provide fallback test cases if generation fails to parse
    return [
        {"type": "VISIBLE", "input_args": "[1, 2, 3], 2", "expected_output": "1", "description": "Basic search"},
        {"type": "VISIBLE", "input_args": "[1, 3, 5], 1", "expected_output": "0", "description": "First element"},
        {"type": "HIDDEN", "input_args": "[1, 2, 4], 5", "expected_output": "-1", "description": "Element not found"},
    ]
