"""
Dashboard statistics endpoints.
Provides real-time counts for the studio dashboard stat cards.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_client_id, get_db
from db.models import Question

router = APIRouter()


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns aggregated question metrics grouped by status.
    RLS ensures only current client's questions are queried.
    """
    counts = {}
    if db is not None:
        try:
            stmt = (
                select(Question.status, func.count(Question.id))
                .group_by(Question.status)
            )
            result = await db.execute(stmt)
            rows = result.all()
            counts = {status: count for status, count in rows}
        except Exception as e:
            print(f"[Dashboard API] DB offline/unreachable: {e}")

    total_generated = sum(counts.values())
    awaiting_review = counts.get("AWAITING_REVIEW", 0)
    approved = counts.get("APPROVED", 0)
    needs_review = counts.get("NEEDS_HUMAN_REVIEW", 0)
    qa_failed = counts.get("QA_FAILED", 0)
    processing = counts.get("PROCESSING", 0)
    upload_queued = counts.get("UPLOAD_QUEUED", 0)
    uploaded = counts.get("UPLOADED", 0)

    return {
        "generated": total_generated,
        "qa_passed": awaiting_review + approved,
        "awaiting_review": awaiting_review,
        "approved": approved,
        "needs_review": needs_review + qa_failed,
        "processing": processing,
        "upload_queued": upload_queued,
        "uploaded": uploaded,
        "breakdown": counts,
    }
