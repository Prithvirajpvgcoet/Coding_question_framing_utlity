import asyncio
from workers.celery_app import celery_app
from orchestrator.graph import workflow

@celery_app.task(bind=True)
def run_question_generation(self, question_id: str, state: dict):
    print(f'[Celery] Received task for question: {question_id}')
    final_state = asyncio.run(workflow.ainvoke(state))
    print(f'[Celery] Task complete for question: {question_id}')
    return final_state
