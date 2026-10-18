import datetime
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_client_id, get_db
from db.models import Question

router = APIRouter()


class GenerateRequest(BaseModel):
    topic:                  str
    subtopic:               str = ""
    difficulty:             str = "MEDIUM"
    question_type:          str = "ALGORITHMIC"
    target_language:        str = "python"
    max_solve_time_minutes: int = 30
    bank_id:                Optional[str] = None
    custom_constraints:     List[str] = []


class GenerateResponse(BaseModel):
    request_id:                   str
    question_id:                  str
    status:                       str
    estimated_completion_seconds: int
    poll_url:                     str
    stream_url:                   str


class BatchGenerateRequest(BaseModel):
    items: List[GenerateRequest]


class BatchGenerateResponse(BaseModel):
    batch_id:   str
    count:      int
    items:      List[GenerateResponse]


def _build_initial_state(req: GenerateRequest, request_id: str, question_id: str, client_id: str) -> dict:
    now = datetime.datetime.now(datetime.UTC).isoformat()
    return {
        "request_id":           request_id,
        "question_id":          question_id,
        "client_id":            client_id,
        "version":              1,
        "status":               "PROCESSING",
        "current_agent":        "",
        "retry_counts":         {},
        "internal_retry_count": 0,
        "revision_count":       0,
        "error_log":            [],
        "requirements": {
            "topic":                  req.topic,
            "subtopic":               req.subtopic,
            "difficulty":             req.difficulty,
            "question_type":          req.question_type,
            "target_language":        req.target_language,
            "max_solve_time_minutes": req.max_solve_time_minutes,
            "custom_constraints":     req.custom_constraints,
            "raw_request":            req.model_dump_json(),
        },
        "agent_run_ids": [],
        "created_at":    now,
        "updated_at":    now,
    }


async def _save_initial_question(db: AsyncSession, q_uuid: uuid.UUID, c_uuid: uuid.UUID, b_uuid: Optional[uuid.UUID], initial_state: dict):
    try:
        new_q = Question(
            id=q_uuid,
            client_id=c_uuid,
            bank_id=b_uuid,
            version=1,
            status="PROCESSING",
            state=initial_state,
            created_at=datetime.datetime.now(datetime.UTC),
        )
        db.add(new_q)
        await db.commit()
    except Exception:
        # If DB connection fails or table doesn't exist yet, do not block generation enqueue
        pass


@router.post("/generate", response_model=GenerateResponse, status_code=202)
async def generate_question(
    req: GenerateRequest,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    request_id  = str(uuid.uuid4())
    question_id = str(uuid.uuid4())

    try:
        c_uuid = uuid.UUID(client_id)
    except ValueError:
        c_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")

    b_uuid = None
    if req.bank_id:
        try:
            b_uuid = uuid.UUID(req.bank_id)
        except ValueError:
            b_uuid = None

    initial_state = _build_initial_state(req, request_id, question_id, client_id)

    # Persist initial record in DB
    await _save_initial_question(db, uuid.UUID(question_id), c_uuid, b_uuid, initial_state)

    # Enqueue Celery task
    from workers.tasks import run_question_generation
    run_question_generation.delay(question_id, initial_state)

    return GenerateResponse(
        request_id=request_id,
        question_id=question_id,
        status="PROCESSING",
        estimated_completion_seconds=120,
        poll_url=f"/api/v1/status/{question_id}",
        stream_url=f"/api/v1/stream/{question_id}",
    )


@router.post("/generate/batch", response_model=BatchGenerateResponse, status_code=202)
async def generate_batch(
    req: BatchGenerateRequest,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    batch_id = str(uuid.uuid4())
    responses = []

    try:
        c_uuid = uuid.UUID(client_id)
    except ValueError:
        c_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")

    from workers.tasks import run_question_generation

    for item in req.items:
        req_id = str(uuid.uuid4())
        q_id   = str(uuid.uuid4())

        b_uuid = None
        if item.bank_id:
            try:
                b_uuid = uuid.UUID(item.bank_id)
            except ValueError:
                b_uuid = None

        state = _build_initial_state(item, req_id, q_id, client_id)
        await _save_initial_question(db, uuid.UUID(q_id), c_uuid, b_uuid, state)

        run_question_generation.delay(q_id, state)

        responses.append(
            GenerateResponse(
                request_id=req_id,
                question_id=q_id,
                status="PROCESSING",
                estimated_completion_seconds=120,
                poll_url=f"/api/v1/status/{q_id}",
                stream_url=f"/api/v1/stream/{q_id}",
            )
        )

    return BatchGenerateResponse(
        batch_id=batch_id,
        count=len(responses),
        items=responses,
    )
