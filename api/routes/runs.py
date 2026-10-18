"""
Runs endpoints for monitoring active generations and inspecting agent execution steps.
"""
import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_client_id, get_db
from db.models import Question, AgentRun

router = APIRouter()


@router.get("/runs")
async def list_runs(
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """
    List all generation runs for the client.
    A run represents a question pipeline execution.
    """
    if db is None:
        return []

    try:
        result = await db.execute(
            select(Question)
            .order_by(Question.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        questions = result.scalars().all()
    except Exception as e:
        print(f"[Runs API] DB offline/unreachable: {e}")
        return []

    runs = []
    for q in questions:
        state = q.state or {}
        reqs = state.get("requirements", {})
        q_meta = state.get("question", {})
        runs.append({
            "run_id": str(q.id),
            "question_id": str(q.id),
            "title": q_meta.get("title") or f"{reqs.get('topic', 'Coding')} Question",
            "topic": reqs.get("topic", ""),
            "difficulty": reqs.get("difficulty", "MEDIUM"),
            "language": reqs.get("target_language", "python"),
            "status": q.status,
            "current_agent": state.get("current_agent", ""),
            "internal_retries": state.get("internal_retry_count", 0),
            "revision_count": state.get("revision_count", 0),
            "created_at": q.created_at.isoformat() if q.created_at else None,
            "updated_at": q.updated_at.isoformat() if q.updated_at else None,
        })

    return runs


@router.get("/runs/{run_id}")
async def get_run_details(
    run_id: str,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve full execution trace and agent steps for a specific run.
    """
    try:
        q_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run_id format")

    q_res = await db.execute(select(Question).where(Question.id == q_uuid))
    question = q_res.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Run not found")

    # Fetch all agent runs for this question
    runs_res = await db.execute(
        select(AgentRun)
        .where(AgentRun.question_id == q_uuid)
        .order_by(AgentRun.created_at.asc())
    )
    agent_runs = runs_res.scalars().all()

    steps = [
        {
            "id": str(ar.id),
            "agent_name": ar.agent_name,
            "model": ar.model,
            "internal_step": ar.internal_step,
            "status": ar.status,
            "input_tokens": ar.input_tokens or 0,
            "output_tokens": ar.output_tokens or 0,
            "cost_usd": ar.cost_usd or 0.0,
            "latency_ms": ar.latency_ms or 0,
            "error_detail": ar.error_detail,
            "created_at": ar.created_at.isoformat() if ar.created_at else None,
        }
        for ar in agent_runs
    ]

    return {
        "run_id": str(question.id),
        "question_id": str(question.id),
        "status": question.status,
        "state": question.state,
        "version": question.version,
        "steps": steps,
        "created_at": question.created_at.isoformat() if question.created_at else None,
        "updated_at": question.updated_at.isoformat() if question.updated_at else None,
    }


@router.delete("/runs/{run_id}")
async def cancel_run(
    run_id: str,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel an in-flight run and revoke the corresponding Celery task if running.
    """
    try:
        q_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run_id format")

    now = datetime.datetime.now(datetime.UTC)
    stmt = (
        update(Question)
        .where(Question.id == q_uuid)
        .values(status="CANCELLED", updated_at=now)
    )
    res = await db.execute(stmt)
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Run not found")

    await db.commit()

    # Attempt Celery task revoke
    try:
        from workers.celery_app import celery_app
        celery_app.control.revoke(run_id, terminate=True)
    except Exception:
        pass

    return {"status": "CANCELLED", "run_id": run_id}
