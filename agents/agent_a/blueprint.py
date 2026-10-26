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

    learning_objs = curriculum.get("learning_objectives", []) if isinstance(curriculum, dict) else []

    user_prompt = f"""Design a question blueprint for:
Topic: {requirements.get('topic')} / {requirements.get('subtopic', '')}
Difficulty: {requirements.get('difficulty')}
Language: {requirements.get('target_language')}
Question type: {requirements.get('question_type')}
Max solve time: {requirements.get('max_solve_time_minutes')} minutes
Custom constraints: {', '.join(requirements.get('custom_constraints', [])) or 'None'}
Learning objectives: {', '.join(learning_objs)}
Client style: {client_config.get('question_style', 'standard')}{refs_text}{revision_text}

You must return a JSON object with at least:
"scenario", "problem_core", "constraints", "expected_complexity", "key_concepts", "approach_hint", "example_scenario", "style_notes", "originality_angle".
"""

    content, usage = await groq_chat(
        model=MODEL_STRONG,
        system=SYSTEM,
        user=user_prompt,
        agent_name="agent_a.blueprint",
        temperature=0.75,
        json_mode=True,
    )

    try:
        raw_obj = json.loads(_clean_json(content))
        if isinstance(raw_obj, dict):
            blueprint = raw_obj
        else:
            blueprint = {}
    except (json.JSONDecodeError, ValueError):
        blueprint = {}

    # Guarantee key required fields exist even if LLM uses alternate field names
    if "scenario" not in blueprint:
        blueprint["scenario"] = (
            blueprint.get("description")
            or blueprint.get("problem_statement")
            or blueprint.get("problem_core")
            or f"Real-world application of {requirements.get('topic', 'Algorithms')}."
        )

    if "problem_core" not in blueprint:
        blueprint["problem_core"] = blueprint.get("scenario") or f"Solve {requirements.get('topic')} problem efficiently."

    if "constraints" not in blueprint:
        blueprint["constraints"] = ["1 <= n <= 10^5"]

    if "expected_complexity" not in blueprint:
        blueprint["expected_complexity"] = {"time": "O(n)", "space": "O(1)"}

    if "key_concepts" not in blueprint:
        blueprint["key_concepts"] = [requirements.get("topic", "algorithms")]

    if "approach_hint" not in blueprint:
        blueprint["approach_hint"] = "optimal traversal or transformation"

    if "example_scenario" not in blueprint:
        blueprint["example_scenario"] = {"input_description": "sample input", "output_description": "sample output"}

    blueprint["_blueprint_usage"] = usage
    return blueprint
