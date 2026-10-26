"""
Run full workflow and persist final state to DB.
"""
import asyncio
import datetime
import uuid

from sqlalchemy import update, select

from workers.celery_app import celery_app
from orchestrator.graph import workflow
from db.session import get_session
from db.models import Question, QuestionVersion


def _to_uuid(val) -> uuid.UUID:
    """Helper to safely parse UUID."""
    if isinstance(val, uuid.UUID):
        return val
    return uuid.UUID(str(val))


async def _generate_and_save(question_id: str, state: dict) -> dict:
    """Run full workflow and persist final state to DB."""
    q_uuid = _to_uuid(question_id)
    c_uuid = _to_uuid(state.get("client_id", "00000000-0000-0000-0000-000000000001"))

    # Ensure Question row exists in DB before pipeline starts logging agent runs
    async with get_session() as db:
        res = await db.execute(select(Question).where(Question.id == q_uuid))
        existing_q = res.scalar_one_or_none()
        if not existing_q:
            db.add(Question(
                id=q_uuid,
                client_id=c_uuid,
                version=1,
                status="PROCESSING",
                state=state,
                created_at=datetime.datetime.now(datetime.timezone.utc),
                updated_at=datetime.datetime.now(datetime.timezone.utc),
            ))
            await db.commit()

    final_state = await workflow.ainvoke(state)

    async with get_session() as db:
        stmt = update(Question).where(Question.id == q_uuid).values(
            state=final_state,
            status=final_state.get("status", "AWAITING_REVIEW"),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        await db.execute(stmt)
        await db.commit()

    return final_state


@celery_app.task(bind=True)
def run_question_generation(self, question_id: str, state: dict):
    print(f"[Celery] Received task for question: {question_id}")
    final_state = asyncio.run(_generate_and_save(question_id, state))
    print(f"[Celery] Task complete for question: {question_id}")
    return final_state


async def _feedback_revision(question_id: str, feedback_text: str) -> None:
    """Load current state, inject human feedback, run Agent E -> F path."""
    from agents.agent_e import run as run_e
    from agents.agent_f import run as run_f
    from orchestrator.edges import route_after_agent_f
    from orchestrator.graph import build_graph

    q_uuid = _to_uuid(question_id)

    # Load current state from DB
    async with get_session() as db:
        result = await db.execute(select(Question).where(Question.id == q_uuid))
        q = result.scalar_one_or_none()

    if not q:
        print(f"[Celery] Question {question_id} not found for feedback revision.")
        return

    # Initialize state safely without dropping pipeline context
    current_state = dict(q.state or {})
    current_state["question_id"] = str(q.id)
    current_state["client_id"] = str(q.client_id)
    current_state["human_feedback"] = {"feedback_text": feedback_text, "action": "REJECT"}
    current_state["status"] = "PROCESSING"
    current_state["current_agent"] = "agent_e"
    
    # Increment revision cycle count
    rev_count = current_state.get("revision_count", 0) + 1
    current_state["revision_count"] = rev_count

    # Update status to PROCESSING before running
    async with get_session() as db:
        await db.execute(
            update(Question).where(Question.id == q_uuid).values(
                status="PROCESSING",
                updated_at=datetime.datetime.now(datetime.timezone.utc),
            )
        )
        await db.commit()

    # Run Agent E then F by merging updates instead of full-state overwriting
    e_updates = await run_e(current_state)
    current_state.update(e_updates)

    f_updates = await run_f(current_state)
    current_state.update(f_updates)

    # Now dispatch to the correct re-entry node
    target = route_after_agent_f(current_state)
    print(f"[Celery] Feedback revision re-entering at: {target}")

    # Build and run the workflow from the targeted re-entry point
    revision_graph = build_graph(entry_point=target)
    final_state = await revision_graph.ainvoke(current_state)

    # Save snapshot to QuestionVersion and update Question
    async with get_session() as db:
        # Fetch current version number
        res = await db.execute(select(Question.version).where(Question.id == q_uuid))
        curr_ver = res.scalar_one_or_none() or 1
        new_ver = curr_ver + 1

        db.add(
            QuestionVersion(
                question_id=q_uuid,
                version=new_ver,
                triggered_by="human_feedback",
                re_entry_agent=target,
                state_snapshot=final_state,
                state_diff={"feedback_text": feedback_text, "target": target},
                created_at=datetime.datetime.now(datetime.timezone.utc),
            )
        )

        await db.execute(
            update(Question).where(Question.id == q_uuid).values(
                state=final_state,
                status=final_state.get("status", "AWAITING_REVIEW"),
                updated_at=datetime.datetime.now(datetime.timezone.utc),
                version=new_ver,
            )
        )
        await db.commit()

    print(f"[Celery] Feedback revision complete for question: {question_id}")


@celery_app.task(bind=True)
def run_feedback_revision(self, question_id: str, feedback_text: str):
    print(f"[Celery] Starting feedback revision for: {question_id}")
    asyncio.run(_feedback_revision(question_id, feedback_text))
