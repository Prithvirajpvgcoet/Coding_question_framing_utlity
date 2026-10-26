"""
Run detail and cancellation endpoints.
"""
import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_client_id, get_db
from db.models import Question, AgentRun

router = APIRouter()


@router.get("/runs")
async def list_runs(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """List questions/runs for the client with optional status filter."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    try:
        c_uuid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client_id")

    query = select(Question).where(Question.client_id == c_uuid)
    if status:
        query = query.where(Question.status == status.upper())

    query = query.order_by(Question.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    questions = result.scalars().all()

    runs_data = [
        {
            "run_id": str(q.id),
            "question_id": str(q.id),
            "status": q.status,
            "version": q.version,
            "created_at": q.created_at.isoformat() if q.created_at else None,
            "updated_at": q.updated_at.isoformat() if q.updated_at else None,
            "topic": (q.state or {}).get("requirements", {}).get("topic"),
            "difficulty": (q.state or {}).get("requirements", {}).get("difficulty"),
            "current_agent": (q.state or {}).get("current_agent"),
        }
        for q in questions
    ]

    return runs_data


@router.get("/runs/{run_id}")
async def get_run_details(
    run_id: str,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """Get full details of a single run including agent_runs history."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    try:
        q_uuid = uuid.UUID(run_id)
        c_uuid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run_id")

    res = await db.execute(select(Question).where(Question.id == q_uuid, Question.client_id == c_uuid))
    q = res.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Run not found")

    # Fetch agent runs
    ar_res = await db.execute(
        select(AgentRun)
        .where(AgentRun.question_id == q_uuid)
        .order_by(AgentRun.created_at.asc())
    )
    agent_runs = ar_res.scalars().all()

    state = q.state or {}
    return {
        "run_id": str(q.id),
        "question_id": str(q.id),
        "status": q.status,
        "version": q.version,
        "current_agent": state.get("current_agent"),
        "created_at": q.created_at.isoformat() if q.created_at else None,
        "updated_at": q.updated_at.isoformat() if q.updated_at else None,
        "state": state,
        "state_summary": {
            "topic": state.get("requirements", {}).get("topic"),
            "difficulty": state.get("requirements", {}).get("difficulty"),
            "target_language": state.get("requirements", {}).get("target_language"),
            "sandbox_passed": state.get("execution", {}).get("all_passed"),
            "aggregate_score": state.get("final_qa", {}).get("aggregate_score"),
            "retries": state.get("retry_counts", {}),
        },
        "agent_runs": [
            {
                "agent_name": ar.agent_name,
                "model": ar.model,
                "status": ar.status,
                "latency_ms": ar.latency_ms,
                "cost_usd": ar.cost_usd,
                "created_at": ar.created_at.isoformat() if ar.created_at else None,
            }
            for ar in agent_runs
        ],
    }


@router.post("/runs/{run_id}/cancel")
async def cancel_run(
    run_id: str,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel an in-flight run and revoke the corresponding Celery task if running.
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    try:
        q_uuid = uuid.UUID(run_id)
        c_uuid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run_id format")

    now = datetime.datetime.now(datetime.timezone.utc)
    stmt = (
        update(Question)
        .where(Question.id == q_uuid, Question.client_id == c_uuid)
        .values(status="CANCELLED", updated_at=now)
    )
    res = await db.execute(stmt)
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Run not found or unauthorized")

    await db.commit()

    # Attempt Celery task revoke
    try:
        from workers.celery_app import celery_app
        celery_app.control.revoke(run_id, terminate=True)
    except Exception:
        pass

    return {"status": "CANCELLED", "run_id": run_id}
