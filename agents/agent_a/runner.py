"""
Agent A - Intake & Blueprint
Wires 4 internal sub-steps with real Groq LLM calls.
"""
from agents.base import utcnow
from agents.agent_a.intake     import extract_requirements
from agents.agent_a.curriculum import map_topic
from agents.agent_a.blueprint  import design_blueprint
from services.client_config    import load_client_config
from orchestrator.state        import QuestionStateObject


async def run(state: QuestionStateObject) -> dict:
    q_id      = state.get("question_id", "")
    client_id = state.get("client_id",   "")
    reqs_in   = state.get("requirements", {})
    print(f"[Agent A] Starting - q:{q_id}")

    # Step 1: Extract / validate requirements
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
    print(f"[Agent A] Curriculum: {curriculum['learning_objectives']}")

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
    print(f"[Agent A] Blueprint: {blueprint.get('scenario', '')[:80]}...")

    # Log agent runs
    import asyncio
    from observability.agent_logger import log_agent_run
    request_id = state.get("request_id", "")
    if usage_intake:
        asyncio.ensure_future(log_agent_run(
            question_id=q_id, request_id=request_id,
            agent_name="agent_a.intake", usage=usage_intake,
            internal_step=True,
        ))
    asyncio.ensure_future(log_agent_run(
        question_id=q_id, request_id=request_id,
        agent_name="agent_a.blueprint", usage=usage_bp,
    ))

    return {
        "current_agent": "agent_a",
        "updated_at":    utcnow(),
        "requirements":  requirements,
        "curriculum":    curriculum,
        "client_config": client_config,
        "blueprint":     blueprint,
    }