"""
Feedback endpoint: APPROVE and REJECT.
APPROVE -> sets status to APPROVED in DB, inserts Feedback audit log.
REJECT  -> persists feedback, sets status to NEEDS_HUMAN_REVIEW, enqueues revision Celery task.
"""
import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import update, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_client_id, get_db
from db.models import Question, Feedback

router = APIRouter()


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
        c_uuid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid question_id or client_id format")

    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    # Verify question exists and belongs to the requesting client
    res = await db.execute(select(Question).where(Question.id == q_uuid))
    q = res.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    if q.client_id != c_uuid:
        raise HTTPException(status_code=403, detail="Forbidden: Question belongs to a different client")

    now = datetime.datetime.now(datetime.timezone.utc)

    if req.action == "APPROVE":
        stmt = update(Question).where(Question.id == q_uuid).values(status="APPROVED", updated_at=now)
        await db.execute(stmt)

        # Insert audit record in feedbacks table
        db.add(Feedback(
            question_id=q_uuid,
            client_id=c_uuid,
            action="APPROVE",
            feedback_text=req.feedback_text,
            created_at=now,
        ))

        await db.commit()
        return {"status": "APPROVED", "question_id": req.question_id}

    if req.action == "REJECT":
        if not req.feedback_text.strip():
            raise HTTPException(status_code=400, detail="feedback_text required for REJECT action")

        stmt = update(Question).where(Question.id == q_uuid).values(
            status="NEEDS_HUMAN_REVIEW", updated_at=now
        )
        await db.execute(stmt)

        # Insert feedback audit record
        db.add(Feedback(
            question_id=q_uuid,
            client_id=c_uuid,
            action="REJECT",
            feedback_text=req.feedback_text,
            created_at=now,
        ))
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
    results = []
    for qid in req.question_ids:
        try:
            res = await submit_feedback(
                FeedbackRequest(question_id=qid, action=req.action, feedback_text=req.feedback_text),
                client_id=client_id,
                db=db,
            )
            results.append(res)
        except HTTPException as e:
            results.append({"question_id": qid, "error": e.detail, "status": "FAILED"})
    return {"results": results}
