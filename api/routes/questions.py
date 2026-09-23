from fastapi import APIRouter, Depends
from api.deps import get_client_id

router = APIRouter()


@router.get("/questions/{question_id}")
async def get_question(
    question_id: str,
    client_id:   str = Depends(get_client_id),
):
    # TODO Phase 2: return full QSO from DB (RLS enforced)
    return {"question_id": question_id, "state": {}}


@router.get("/questions/{question_id}/preview")
async def get_preview(
    question_id: str,
    client_id:   str = Depends(get_client_id),
):
    # TODO Phase 2: return just the HTML field from state
    return {"html": "<p>stub preview</p>"}


@router.get("/questions/{question_id}/versions")
async def get_versions(
    question_id: str,
    client_id:   str = Depends(get_client_id),
):
    # TODO Phase 6: return version history from question_versions table
    return {"question_id": question_id, "versions": []}


@router.get("/questions/{question_id}/score")
async def get_score(
    question_id: str,
    client_id:   str = Depends(get_client_id),
):
    # TODO Phase 5: return quality score breakdown
    return {"question_id": question_id, "aggregate_score": None, "sub_scores": {}}