"""
Step 4: Design question blueprint.
Model: llama-3.3-70b-versatile — needs strong reasoning + creativity.
"""
import json
import re
from agents.base import groq_chat, load_prompt, MODEL_STRONG

SYSTEM = load_prompt("agent_a_blueprint")


def _clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def design_blueprint(
    requirements: dict,
    curriculum:   dict,
    client_config: dict,
    references:   list,
    revision_instruction: str = "",
) -> dict:
    """
    Generate a structured question blueprint.
    revision_instruction: injected by Agent F when revising scope.
    """
    refs_text = ""
    if references:
        refs_text = "\n\nExisting reference questions (DO NOT copy these):\n"
        for r in references[:3]:
            refs_text += f"- {r.get('title', 'Unknown')}: {r.get('excerpt', '')}\n"

    revision_text = ""
    if revision_instruction:
        revision_text = f"\n\nREVISION INSTRUCTION (must follow): {revision_instruction}"

    user_prompt = f"""Design a question blueprint for:
Topic: {requirements.get('topic')} / {requirements.get('subtopic', '')}
Difficulty: {requirements.get('difficulty')}
Language: {requirements.get('target_language')}
Question type: {requirements.get('question_type')}
Max solve time: {requirements.get('max_solve_time_minutes')} minutes
Custom constraints: {', '.join(requirements.get('custom_constraints', [])) or 'None'}
Learning objectives: {', '.join(curriculum.get('learning_objectives', []))}
Client style: {client_config.get('question_style', 'standard')}{refs_text}{revision_text}"""

    content, usage = await groq_chat(
        model=MODEL_STRONG,
        system=SYSTEM,
        user=user_prompt,
        agent_name="agent_a.blueprint",
        temperature=0.75,
        json_mode=True,
    )

    try:
        blueprint = json.loads(_clean_json(content))
    except (json.JSONDecodeError, ValueError):
        blueprint = {
            "scenario":   "Parse error — fallback scenario",
            "problem_core": requirements.get("topic", "Arrays") + " problem",
            "constraints": ["1 <= n <= 10^5"],
            "expected_complexity": {"time": "O(n)", "space": "O(1)"},
            "key_concepts": [requirements.get("topic", "arrays")],
            "approach_hint": "brute force then optimize",
            "example_scenario": {"input_description": "stub", "output_description": "stub"},
            "style_notes": "standard",
            "originality_angle": "unique twist on classic problem",
        }

    blueprint["_blueprint_usage"] = usage
    return blueprint