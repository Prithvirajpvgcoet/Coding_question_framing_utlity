import datetime
from uuid import uuid4
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.deps import get_client_id

router = APIRouter()


class GenerateRequest(BaseModel):
    topic:                  str
    subtopic:               str = ""
    difficulty:             str = "MEDIUM"
    question_type:          str = "ALGORITHMIC"
    target_language:        str = "python"
    max_solve_time_minutes: int = 30


class GenerateResponse(BaseModel):
    request_id:                   str
    question_id:                  str
    status:                       str
    estimated_completion_seconds: int
    poll_url:                     str
    stream_url:                   str


@router.post("/generate", response_model=GenerateResponse, status_code=202)
async def generate_question(
    req: GenerateRequest,
    client_id: str = Depends(get_client_id),
):
    request_id  = str(uuid4())
    question_id = str(uuid4())
    now         = datetime.datetime.utcnow().isoformat()

    initial_state = {
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
            "raw_request":            req.model_dump_json(),
        },
        "agent_run_ids": [],
        "created_at":    now,
        "updated_at":    now,
    }

    # TODO Phase 2: persist initial_state to questions table in DB

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