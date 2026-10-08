import asyncio
import datetime
from sqlalchemy import update
from workers.celery_app import celery_app
from orchestrator.graph import workflow
from db.session import get_session
from db.models import Question

async def run_and_save(question_id: str, state: dict):
    # 1. Run workflow
    final_state = await workflow.ainvoke(state)
    
    # 2. Save final state to DB
    async with get_session() as db:
        stmt = update(Question).where(Question.id == question_id).values(
            state=final_state,
            status=final_state.get("status", "PROCESSING"),
            updated_at=datetime.datetime.now(datetime.UTC)
        )
        await db.execute(stmt)
        await db.commit()
    return final_state

@celery_app.task(bind=True)
def run_question_generation(self, question_id: str, state: dict):
    print(f'[Celery] Received task for question: {question_id}')
    final_state = asyncio.run(run_and_save(question_id, state))
    print(f'[Celery] Task complete for question: {question_id}')
    return final_state
