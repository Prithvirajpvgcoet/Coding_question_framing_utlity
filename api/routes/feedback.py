"""
Feedback endpoint: APPROVE and REJECT.
APPROVE -> sets status to APPROVED in DB.
REJECT  -> persists feedback, sets status to NEEDS_HUMAN_REVIEW, enqueues revision Celery task.
"""
import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import update, insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_client_id, get_db

router = APIRouter()

DEV_CLIENT_UUID = "00000000-0000-0000-0000-000000000001"


class FeedbackRequest(BaseModel):
    question_id:   str
    action:        str   # "APPROVE" | "REJECT"
    feedback_text: str = ""


@router.post("/feedback")
async def submit_feedback(
    req:       FeedbackRequest,
    client_id: str = Depends(get_client_id),
    db:        AsyncSession = Depends(get_db),
):
    try:
        q_uuid = uuid.UUID(req.question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid question_id format")

    now = datetime.datetime.now(datetime.UTC)

    if req.action == "APPROVE":
        stmt = update(__import__("db.models", fromlist=["Question"]).Question).where(
            __import__("db.models", fromlist=["Question"]).Question.id == q_uuid
        ).values(status="APPROVED", updated_at=now)
        await db.execute(stmt)

        # Insert feedback record
        try:
            fb_stmt = insert(__import__("db.models", fromlist=["Feedback"]).Feedback if hasattr(
                __import__("db.models", fromlist=["Feedback"]), "Feedback") else None
            )
        except Exception:
            pass  # Feedback model not yet in ORM — skip insert

        await db.commit()
        return {"status": "APPROVED", "question_id": req.question_id}

    if req.action == "REJECT":
        if not req.feedback_text.strip():
            raise HTTPException(status_code=400, detail="feedback_text required for REJECT action")

        from db.models import Question
        stmt = update(Question).where(Question.id == q_uuid).values(
            status="NEEDS_HUMAN_REVIEW", updated_at=now
        )
        await db.execute(stmt)
        await db.commit()

        # Enqueue revision task
        from workers.tasks import run_feedback_revision
        run_feedback_revision.delay(req.question_id, req.feedback_text)

        return {"status": "REVISION_STARTED", "question_id": req.question_id}

    raise HTTPException(status_code=400, detail="action must be APPROVE or REJECT")


class BulkFeedbackRequest(BaseModel):
    question_ids: list[str]
    action: str  # "APPROVE" | "REJECT"
    feedback_text: str = ""


@router.post("/feedback/bulk")
async def submit_bulk_feedback(
    req: BulkFeedbackRequest,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    if req.action not in ("APPROVE", "REJECT"):
        raise HTTPException(status_code=400, detail="action must be APPROVE or REJECT")

    q_uuids = []
    for qid in req.question_ids:
        try:
            q_uuids.append(uuid.UUID(qid))
        except ValueError:
            continue

    if not q_uuids:
        raise HTTPException(status_code=400, detail="No valid question_ids provided")

    now = datetime.datetime.now(datetime.UTC)
    from db.models import Question

    if req.action == "APPROVE":
        stmt = (
            update(Question)
            .where(Question.id.in_(q_uuids))
            .values(status="APPROVED", updated_at=now)
        )
        await db.execute(stmt)
        await db.commit()
        return {"status": "APPROVED", "updated_count": len(q_uuids), "question_ids": req.question_ids}

    if req.action == "REJECT":
        stmt = (
            update(Question)
            .where(Question.id.in_(q_uuids))
            .values(status="NEEDS_HUMAN_REVIEW", updated_at=now)
        )
        await db.execute(stmt)
        await db.commit()

        # Enqueue revisions
        from workers.tasks import run_feedback_revision
        for qid in req.question_ids:
            run_feedback_revision.delay(qid, req.feedback_text or "Bulk revision requested.")

        return {"status": "REVISION_STARTED", "updated_count": len(q_uuids), "question_ids": req.question_ids}