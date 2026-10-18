"""
Celery background tasks for automating iMocha question uploads.
"""
import asyncio
import datetime
import uuid

from sqlalchemy import select, update
from workers.celery_app import celery_app
from db.session import get_session
from db.models import UploadJob, Question
from services.imocha_uploader import build_imocha_payload, validate_upload_payload
from services.playwright_session import PlaywrightUploadSession


async def _process_upload(upload_job_id: str) -> dict:
    job_uuid = uuid.UUID(upload_job_id)
    now = datetime.datetime.now(datetime.UTC)

    async with get_session() as db:
        res = await db.execute(select(UploadJob).where(UploadJob.id == job_uuid))
        job = res.scalar_one_or_none()
        if not job:
            return {"status": "FAILED", "error": "UploadJob not found"}

        # Set status to IN_PROGRESS
        job.status = "IN_PROGRESS"
        job.started_at = now
        await db.commit()

        # Load Question
        q_res = await db.execute(select(Question).where(Question.id == job.question_id))
        question = q_res.scalar_one_or_none()
        if not question or not question.state:
            job.status = "FAILED"
            job.error = "Question state missing"
            await db.commit()
            return {"status": "FAILED", "error": job.error}

        payload = build_imocha_payload(question.state, bank_id=job.bank_id or "default")
        is_valid, validation_errors = validate_upload_payload(payload)

        if not is_valid:
            job.status = "FAILED"
            job.error = "; ".join(validation_errors)
            job.payload_json = payload
            await db.commit()
            return {"status": "FAILED", "error": job.error}

        # Run automated upload session
        driver = PlaywrightUploadSession(headless=True)
        upload_res = await driver.execute_upload(payload)

        # Mark COMPLETED
        job.status = "COMPLETED"
        job.payload_json = payload
        job.steps_log = upload_res.get("steps", [])
        job.completed_at = datetime.datetime.now(datetime.UTC)

        # Update Question status to UPLOADED
        await db.execute(
            update(Question)
            .where(Question.id == job.question_id)
            .values(status="UPLOADED", updated_at=datetime.datetime.now(datetime.UTC))
        )
        await db.commit()

    return {"status": "COMPLETED", "job_id": upload_job_id}


@celery_app.task(bind=True)
def run_upload_job(self, upload_job_id: str):
    """Celery task entry point for executing an upload job."""
    print(f"[Celery] Processing upload job: {upload_job_id}")
    result = asyncio.run(_process_upload(upload_job_id))
    print(f"[Celery] Upload job {upload_job_id} finished with status: {result.get('status')}")
    return result
