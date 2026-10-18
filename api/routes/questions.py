"""
Question detail, preview, versions, and score endpoints.
All backed by real DB queries with RLS enforced via get_db().
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.deps import get_client_id, get_db
from db.models import Question, QuestionVersion

router = APIRouter()


def _get_question_or_404(q):
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return q


async def _fetch(question_id: str, db: AsyncSession):
    try:
        q_uuid = uuid.UUID(question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid question_id format")
    result = await db.execute(select(Question).where(Question.id == q_uuid))
    return _get_question_or_404(result.scalar_one_or_none())


@router.get("/questions")
async def list_questions(
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    if db is None:
        return []

    try:
        result = await db.execute(
            select(Question).order_by(Question.created_at.desc()).limit(limit).offset(offset)
        )
        questions = result.scalars().all()
    except Exception as e:
        print(f"[Questions API] DB offline/unreachable: {e}")
        return []
    return [
        {
            "question_id": str(q.id),
            "status":      q.status,
            "version":     q.version,
            "topic":       (q.state or {}).get("requirements", {}).get("topic", ""),
            "difficulty":  (q.state or {}).get("requirements", {}).get("difficulty", ""),
            "language":    (q.state or {}).get("requirements", {}).get("target_language", ""),
            "created_at":  q.created_at.isoformat() if q.created_at else None,
        }
        for q in questions
    ]


@router.get("/questions/{question_id}")
async def get_question(
    question_id: str,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """Return full question state from DB."""
    q = await _fetch(question_id, db)
    return {
        "question_id": str(q.id),
        "status":      q.status,
        "version":     q.version,
        "state":       q.state,
        "created_at":  q.created_at.isoformat() if q.created_at else None,
        "updated_at":  q.updated_at.isoformat() if q.updated_at else None,
    }


@router.get("/questions/{question_id}/preview")
async def get_preview(
    question_id: str,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """Return rendered HTML and code block for the question."""
    q = await _fetch(question_id, db)
    state = q.state or {}
    html  = state.get("html", {}).get("formatted_question", "")
    code  = state.get("code", {}).get("solution", state.get("solution_code", ""))
    lang  = state.get("code", {}).get("language", "python")
    return {
        "question_id": question_id,
        "html":        html,
        "code":        code,
        "language":    lang,
    }


@router.get("/questions/{question_id}/versions")
async def get_versions(
    question_id: str,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """Return revision history from question_versions table."""
    try:
        q_uuid = uuid.UUID(question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid question_id format")

    result = await db.execute(
        select(QuestionVersion)
        .where(QuestionVersion.question_id == q_uuid)
        .order_by(QuestionVersion.version.asc())
    )
    versions = result.scalars().all()
    return {
        "question_id": question_id,
        "versions": [
            {
                "version":        v.version,
                "triggered_by":   v.triggered_by,
                "re_entry_agent": v.re_entry_agent,
                "created_at":     v.created_at.isoformat() if v.created_at else None,
            }
            for v in versions
        ],
    }


@router.get("/questions/{question_id}/score")
async def get_score(
    question_id: str,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """Return quality score breakdown from the state."""
    q = await _fetch(question_id, db)
    state      = q.state or {}
    quality    = state.get("quality", {})
    final_qa   = state.get("final_qa", {})
    checks     = final_qa.get("deterministic_checks", {})
    return {
        "question_id":     question_id,
        "aggregate_score": final_qa.get("aggregate_score"),
        "quality_pass":    quality.get("pass"),
        "avg_score":       quality.get("avg_score"),
        "sub_scores":      quality.get("scores", {}),
        "failure_reasons": quality.get("failure_reasons", []),
        "deterministic_checks": checks,
    }