"""
Question retrieval endpoints: list, get by ID, preview, versions, score breakdown.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_client_id, get_db
from db.models import Question, QuestionVersion

router = APIRouter()


async def _fetch(question_id: str, client_id: str, db: AsyncSession) -> Question:
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")
    try:
        q_uuid = uuid.UUID(question_id)
        c_uuid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid question_id or client_id")

    res = await db.execute(
        select(Question).where(Question.id == q_uuid, Question.client_id == c_uuid)
    )
    q = res.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return q


@router.get("/questions")
async def list_questions(
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    try:
        c_uuid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client_id")

    try:
        result = await db.execute(
            select(Question)
            .where(Question.client_id == c_uuid)
            .order_by(Question.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        questions = result.scalars().all()
    except Exception as e:
        print(f"[Questions API] DB query error: {e}")
        return []

    return [
        {
            "id": str(q.id),
            "question_id": str(q.id),
            "version": q.version,
            "status": q.status,
            "topic": (q.state or {}).get("requirements", {}).get("topic") or "Algorithmic",
            "subtopic": (q.state or {}).get("requirements", {}).get("subtopic") or "",
            "difficulty": (q.state or {}).get("requirements", {}).get("difficulty") or "MEDIUM",
            "target_language": (q.state or {}).get("requirements", {}).get("target_language") or "python",
            "language": (q.state or {}).get("requirements", {}).get("target_language") or "python",
            "created_at": q.created_at.isoformat() if q.created_at else None,
            "updated_at": q.updated_at.isoformat() if q.updated_at else None,
        }
        for q in questions
    ]


@router.get("/questions/{question_id}")
async def get_question(
    question_id: str,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    q = await _fetch(question_id, client_id, db)
    state = q.state or {}
    question_meta = state.get("question", {})
    return {
        "id": str(q.id),
        "question_id": str(q.id),
        "client_id": str(q.client_id),
        "bank_id": str(q.bank_id) if q.bank_id else None,
        "version": q.version,
        "status": q.status,
        "title": question_meta.get("title") or state.get("blueprint", {}).get("title") or "Algorithmic Question",
        "description_html": state.get("html", {}).get("formatted_question") or question_meta.get("description_html", ""),
        "solution_code": state.get("code", {}).get("solution") or state.get("solution_code", ""),
        "test_cases": state.get("test_cases", []),
        "state": state,
        "created_at": q.created_at.isoformat() if q.created_at else None,
        "updated_at": q.updated_at.isoformat() if q.updated_at else None,
    }


@router.get("/questions/{question_id}/preview")
async def preview_question(
    question_id: str,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    q = await _fetch(question_id, client_id, db)
    state = q.state or {}
    return {
        "question_id": str(q.id),
        "title": state.get("question", {}).get("title", ""),
        "description_html": state.get("html", {}).get("formatted_question", ""),
        "solution_code": state.get("code", {}).get("solution") or state.get("solution_code", ""),
        "target_language": state.get("requirements", {}).get("target_language", "python"),
        "visible_tests": [
            t for t in state.get("test_cases", [])
            if t.get("type") == "VISIBLE"
        ],
        "status": q.status,
        "version": q.version,
    }


@router.get("/questions/{question_id}/versions")
async def get_versions(
    question_id: str,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    q = await _fetch(question_id, client_id, db)
    try:
        q_uuid = uuid.UUID(question_id)
        res = await db.execute(
            select(QuestionVersion)
            .where(QuestionVersion.question_id == q_uuid)
            .order_by(QuestionVersion.version.asc())
        )
        versions = res.scalars().all()
        return [
            {
                "version": v.version,
                "triggered_by": v.triggered_by,
                "re_entry_agent": v.re_entry_agent,
                "state_diff": v.state_diff,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in versions
        ]
    except Exception as e:
        print(f"[Questions API] Versions query error: {e}")
        return []


@router.get("/questions/{question_id}/score")
async def get_score(
    question_id: str,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    q = await _fetch(question_id, client_id, db)
    state = q.state or {}
    quality = state.get("quality", {})
    consistency = state.get("consistency", {})
    final_qa = state.get("final_qa", {})
    
    avg_score = quality.get("avg_score")
    if avg_score is None:
        avg_score = state.get("quality_score", 0.0)

    return {
        "question_id": str(q.id),
        "quality_score": avg_score,
        "quality_passed": quality.get("pass", False),
        "scores_breakdown": quality.get("scores", {}),
        "failure_reasons": quality.get("failure_reasons", []),
        "consistent": consistency.get("consistent", True),
        "consistency_mismatches": consistency.get("mismatches", []),
        "final_qa_approved": final_qa.get("approved", False),
        "aggregate_score": final_qa.get("aggregate_score", 0.0),
    }
