"""
Celery tasks for background question generation and feedback revision.
"""
import asyncio
import datetime

from sqlalchemy import update, select

from workers.celery_app import celery_app
from orchestrator.graph import workflow
from db.session import get_session
from db.models import Question


async def _generate_and_save(question_id: str, state: dict) -> dict:
    """Run full workflow and persist final state to DB."""
    final_state = await workflow.ainvoke(state)

    async with get_session() as db:
        stmt = update(Question).where(Question.id == question_id).values(
            state=final_state,
            status=final_state.get("status", "PROCESSING"),
            updated_at=datetime.datetime.now(datetime.UTC),
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
    from orchestrator.graph import workflow

    # Load current state from DB
    async with get_session() as db:
        result = await db.execute(select(Question).where(Question.id == question_id))
        q = result.scalar_one_or_none()

    if not q:
        print(f"[Celery] Question {question_id} not found for feedback revision.")
        return

    state = dict(q.state or {})
    state["human_feedback"] = {"feedback_text": feedback_text, "action": "REJECT"}
    state["status"] = "PROCESSING"
    state["current_agent"] = "agent_e"

    # Update status to PROCESSING before running
    async with get_session() as db:
        await db.execute(
            update(Question).where(Question.id == question_id).values(
                status="PROCESSING",
                updated_at=datetime.datetime.now(datetime.UTC),
            )
        )
        await db.commit()

    # Run Agent E then F
    state = await run_e(state)
    state = await run_f(state)

    # Now dispatch to the correct re-entry node
    target = route_after_agent_f(state)
    print(f"[Celery] Feedback revision re-entering at: {target}")

    # Run the rest of the workflow from the re-entry point
    final_state = await workflow.ainvoke(state)

    async with get_session() as db:
        await db.execute(
            update(Question).where(Question.id == question_id).values(
                state=final_state,
                status=final_state.get("status", "PROCESSING"),
                updated_at=datetime.datetime.now(datetime.UTC),
                version=Question.version + 1,
            )
        )
        await db.commit()

    print(f"[Celery] Feedback revision complete for question: {question_id}")


@celery_app.task(bind=True)
def run_feedback_revision(self, question_id: str, feedback_text: str):
    print(f"[Celery] Starting feedback revision for: {question_id}")
    asyncio.run(_feedback_revision(question_id, feedback_text))
