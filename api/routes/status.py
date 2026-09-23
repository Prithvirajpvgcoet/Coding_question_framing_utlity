from fastapi import APIRouter, Depends
from api.deps import get_client_id

router = APIRouter()


@router.get("/status/{question_id}")
async def get_status(
    question_id: str,
    client_id:   str = Depends(get_client_id),
):
    # TODO Phase 2: query questions table by question_id + client_id (RLS enforced)
    return {
        "question_id":   question_id,
        "status":        "PROCESSING",
        "current_agent": "stub",
        "version":       1,
        "score":         None,
    }


@router.get("/stream/{question_id}")
async def stream_progress(
    question_id: str,
    client_id:   str = Depends(get_client_id),
):
    """
    Server-Sent Events (SSE) endpoint — streams real-time agent progress.
    Frontend connects here to show live pipeline progress bar.
    """
    from sse_starlette.sse import EventSourceResponse
    import asyncio

    async def event_generator():
        # TODO Phase 2: subscribe to Redis pub/sub channel for this question_id
        # and yield events as agents complete their steps
        yield {"event": "connected", "data": f'{{"question_id": "{question_id}"}}'}
        await asyncio.sleep(1)
        yield {"event": "stub_event", "data": '{"agent": "stub", "status": "running"}'}

    return EventSourceResponse(event_generator())