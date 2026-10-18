"""
Status polling and SSE streaming endpoints.
GET /status/{question_id} - real DB query
GET /stream/{question_id} - DB-polling SSE (no Redis needed)
"""
import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.deps import get_client_id, get_db
from db.models import Question

router = APIRouter()

TERMINAL_STATUSES = {"AWAITING_REVIEW", "APPROVED", "REJECTED", "NEEDS_HUMAN_REVIEW"}


@router.get("/status/{question_id}")
async def get_status(
    question_id: str,
    client_id:   str = Depends(get_client_id),
    db:          AsyncSession = Depends(get_db),
):
    try:
        q_uuid = uuid.UUID(question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid question_id format")

    result = await db.execute(select(Question).where(Question.id == q_uuid))
    q = result.scalar_one_or_none()

    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    state    = q.state or {}
    final_qa = state.get("final_qa", {})
    score    = final_qa.get("aggregate_score")

    return {
        "question_id":   str(q.id),
        "status":        q.status,
        "current_agent": state.get("current_agent", ""),
        "version":       q.version,
        "score":         score,
        "question":      state.get("question") or state.get("generated_question"),
        "created_at":    q.created_at.isoformat() if q.created_at else None,
        "updated_at":    q.updated_at.isoformat() if q.updated_at else None,
    }


@router.get("/stream/{question_id}")
async def stream_progress(
    question_id: str,
    request:     Request,
    api_key:     str = "",   # Query param fallback — browser EventSource can't set headers
):
    """
    Server-Sent Events endpoint. Polls DB every 2s and emits 'progress' events.
    Terminates when question reaches a terminal status or after 3 minutes.

    Auth: reads X-API-Key header OR ?api_key= query param (for browser EventSource).
    """
    from sse_starlette.sse import EventSourceResponse
    from db.session import get_session

    # Auth: prefer header, fall back to query param
    key_from_header = request.headers.get("X-API-Key", "")
    effective_key   = key_from_header or api_key
    if not effective_key:
        from sse_starlette.sse import EventSourceResponse
        async def _unauth():
            yield {"event": "error", "data": json.dumps({"error": "Missing API key"})}
        return EventSourceResponse(_unauth())

    async def event_generator():
        last_agent  = None
        last_status = None

        yield {"event": "connected", "data": json.dumps({"question_id": question_id})}

        for _ in range(90):   # max 3 minutes (90 * 2s)
            await asyncio.sleep(2)
            try:
                async with get_session() as db:
                    try:
                        q_uuid = uuid.UUID(question_id)
                    except ValueError:
                        yield {"event": "error", "data": json.dumps({"error": "Invalid question_id"})}
                        return

                    result = await db.execute(select(Question).where(Question.id == q_uuid))
                    q = result.scalar_one_or_none()

                if not q:
                    yield {"event": "error", "data": json.dumps({"error": "Question not found"})}
                    return

                state  = q.state or {}
                agent  = state.get("current_agent", "")
                status = q.status

                if agent != last_agent or status != last_status:
                    yield {
                        "event": "progress",
                        "data":  json.dumps({
                            "current_agent": agent,
                            "status":        status,
                            "retry_counts":  state.get("retry_counts", {}),
                            "error_log":     state.get("error_log", [])[-3:],  # last 3 errors only
                        })
                    }
                    last_agent  = agent
                    last_status = status

                if status in TERMINAL_STATUSES:
                    yield {"event": "done", "data": json.dumps({"status": status})}
                    return

            except Exception as e:
                yield {"event": "error", "data": json.dumps({"error": str(e)})}
                return

        yield {"event": "timeout", "data": json.dumps({"message": "Polling limit reached."})}

    return EventSourceResponse(event_generator())