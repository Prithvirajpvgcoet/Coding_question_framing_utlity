"""
Agent A — Intake & Syllabus Mapping
Phase 1: real Groq API calls for intake and blueprint.
"""
from agents.base import utcnow
from orchestrator.state import QuestionStateObject
from services.client_config import load_client_config

from .intake import extract_requirements
from .curriculum import map_topic
from .blueprint import design_blueprint

async def run(state: QuestionStateObject) -> dict:
    q_id = state.get("question_id", "unknown")
    print(f"[Agent A] Starting - q:{q_id}")

    client_id = state.get("client_id", "00000000-0000-0000-0000-000000000001")
    reqs_in   = state.get("requirements", {})

    # Step 1: Extract requirements from raw request (if needed)
    raw_request = reqs_in.get("raw_request", "")
    if raw_request and not reqs_in.get("topic"):
        requirements = await extract_requirements(raw_request)
        usage_intake = requirements.pop("_intake_usage", {})
    else:
        requirements = reqs_in
        usage_intake = {}

    print(f"[Agent A] Requirements: {requirements.get('topic')} / "
          f"{requirements.get('difficulty')} / {requirements.get('target_language')}")

    # Step 2: Map topic to curriculum
    curriculum = await map_topic(
        topic=requirements.get("topic", "Arrays"),
        subtopic=requirements.get("subtopic", ""),
    )
    objectives = curriculum.get("learning_objectives", []) if isinstance(curriculum, dict) else []
    print(f"[Agent A] Curriculum: {objectives}")

    # Step 3: Load client config
    client_config = await load_client_config(
        client_id=client_id,
        language=requirements.get("target_language", "python"),
        question_type=requirements.get("question_type", "ALGORITHMIC"),
    )

    # Step 4: Design blueprint
    revision_instruction = state.get("blueprint", {}).get("_revision_instruction", "")
    references           = state.get("references", [])

    blueprint = await design_blueprint(
        requirements=requirements,
        curriculum=curriculum,
        client_config=client_config,
        references=references,
        revision_instruction=revision_instruction,
    )
    usage_bp = blueprint.pop("_blueprint_usage", {})

    print(f"[Agent A] Blueprint: {blueprint.get('scenario', '')[:60]}...")

    # Log agent runs (two steps: intake if ran, blueprint always)
    try:
        from observability.agent_logger import log_agent_run
        if usage_intake:
            await log_agent_run(
                question_id=q_id,
                request_id=state.get("request_id", ""),
                agent_name="agent_a.intake",
                usage=usage_intake,
                status="SUCCESS",
            )
        await log_agent_run(
            question_id=q_id,
            request_id=state.get("request_id", ""),
            agent_name="agent_a.blueprint",
            usage=usage_bp,
            status="SUCCESS",
        )
    except Exception as e:
        print(f"[Agent A] Observability logging notice: {e}")

    return {
        "current_agent":  "agent_a",
        "updated_at":     utcnow(),
        "requirements":   requirements,
        "curriculum":     curriculum,
        "client_config":  client_config,
        "blueprint":      blueprint,
    }
