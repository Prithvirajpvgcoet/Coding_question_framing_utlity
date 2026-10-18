"""
Upload management endpoints.
Manages staging, dispatching, and tracking question uploads into the iMocha platform.
"""
import uuid
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_client_id, get_db
from db.models import UploadJob, Question

router = APIRouter()


class CreateUploadJobRequest(BaseModel):
    question_id: str
    bank_id: Optional[str] = None


class BulkUploadRequest(BaseModel):
    question_ids: List[str]
    bank_id: Optional[str] = None


@router.get("/uploads")
async def list_uploads(
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """
    List all upload jobs.
    """
    if db is None:
        return []

    try:
        stmt = (
            select(UploadJob)
            .order_by(UploadJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await db.execute(stmt)
        jobs = res.scalars().all()
    except Exception as e:
        print(f"[Uploads API] DB query warning (DB offline/unreachable): {e}")
        return []

    return [
        {
            "id": str(job.id),
            "question_id": str(job.question_id),
            "bank_id": job.bank_id,
            "status": job.status,
            "queue_position": job.queue_position,
            "error": job.error,
            "step_count": len(job.steps_log) if job.steps_log else 0,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "created_at": job.created_at.isoformat() if job.created_at else None,
        }
        for job in jobs
    ]


@router.post("/uploads", status_code=202)
async def create_upload_job(
    req: CreateUploadJobRequest,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Queue a question for upload.
    """
    try:
        q_uuid = uuid.UUID(req.question_id)
        c_uuid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    job_id = uuid.uuid4()
    now = datetime.datetime.now(datetime.UTC)

    new_job = UploadJob(
        id=job_id,
        client_id=c_uuid,
        question_id=q_uuid,
        bank_id=req.bank_id,
        status="QUEUED",
        created_at=now,
    )
    db.add(new_job)

    # Update question status to UPLOAD_QUEUED
    await db.execute(
        update(Question)
        .where(Question.id == q_uuid)
        .values(status="UPLOAD_QUEUED", updated_at=now)
    )
    await db.commit()

    # Dispatch background Celery worker
    try:
        from workers.upload_tasks import run_upload_job
        run_upload_job.delay(str(job_id))
    except Exception:
        pass

    return {
        "job_id": str(job_id),
        "question_id": req.question_id,
        "status": "QUEUED",
        "poll_url": f"/api/v1/uploads/{job_id}",
    }


@router.post("/uploads/bulk", status_code=202)
async def create_bulk_uploads(
    req: BulkUploadRequest,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Queue multiple questions for upload.
    """
    try:
        c_uuid = uuid.UUID(client_id)
    except ValueError:
        c_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")

    job_ids = []
    now = datetime.datetime.now(datetime.UTC)

    from workers.upload_tasks import run_upload_job

    for qid in req.question_ids:
        try:
            q_uuid = uuid.UUID(qid)
        except ValueError:
            continue

        job_id = uuid.uuid4()
        job = UploadJob(
            id=job_id,
            client_id=c_uuid,
            question_id=q_uuid,
            bank_id=req.bank_id,
            status="QUEUED",
            created_at=now,
        )
        db.add(job)
        job_ids.append(str(job_id))

        try:
            run_upload_job.delay(str(job_id))
        except Exception:
            pass

    await db.commit()

    return {
        "queued_count": len(job_ids),
        "job_ids": job_ids,
        "status": "QUEUED",
    }


@router.get("/uploads/{job_id}")
async def get_upload_job_details(
    job_id: str,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve full step progression and payload details for an upload job.
    """
    try:
        j_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job_id format")

    res = await db.execute(select(UploadJob).where(UploadJob.id == j_uuid))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Upload job not found")

    return {
        "id": str(job.id),
        "question_id": str(job.question_id),
        "bank_id": job.bank_id,
        "status": job.status,
        "queue_position": job.queue_position,
        "payload_json": job.payload_json,
        "steps_log": job.steps_log,
        "error": job.error,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


@router.post("/uploads/{job_id}/retry", status_code=202)
async def retry_upload_job(
    job_id: str,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Retry a failed upload job.
    """
    try:
        j_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job_id format")

    res = await db.execute(select(UploadJob).where(UploadJob.id == j_uuid))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Upload job not found")

    job.status = "QUEUED"
    job.error = None
    job.started_at = None
    job.completed_at = None
    await db.commit()

    try:
        from workers.upload_tasks import run_upload_job
        run_upload_job.delay(job_id)
    except Exception:
        pass

    return {"status": "QUEUED", "job_id": job_id}
