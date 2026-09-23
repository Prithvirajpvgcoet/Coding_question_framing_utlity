from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.deps import get_client_id

router = APIRouter()


class FeedbackRequest(BaseModel):
    question_id:   str
    action:        str   # "APPROVE" | "REJECT"
    feedback_text: str = ""


@router.post("/feedback")
async def submit_feedback(
    req:       FeedbackRequest,
    client_id: str = Depends(get_client_id),
):
    if req.action == "APPROVE":
        # TODO Phase 6: update questions.status = APPROVED in DB
        return {"status": "APPROVED", "question_id": req.question_id}

    if req.action == "REJECT":
        if not req.feedback_text.strip():
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="feedback_text required for REJECT action")

        # TODO Phase 6: persist feedback record, load current state, trigger revision
        # from workers.tasks import run_feedback_revision
        # run_feedback_revision.delay(req.question_id, state_with_feedback)
        return {"status": "REVISION_STARTED", "question_id": req.question_id}

    from fastapi import HTTPException
    raise HTTPException(status_code=400, detail="action must be APPROVE or REJECT")