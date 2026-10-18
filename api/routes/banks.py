"""
Question bank management routes.
Allows organizing questions into target iMocha or internal banks.
"""
import uuid
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_client_id, get_db
from db.models import QuestionBank, Question

router = APIRouter()


class CreateBankRequest(BaseModel):
    name: str
    description: Optional[str] = None
    imocha_bank_id: Optional[str] = None


class AddQuestionsToBankRequest(BaseModel):
    question_ids: List[str]


@router.get("/banks")
async def list_banks(
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """
    List all question banks with their question counts.
    """
    if db is None:
        return []

    banks_list = []
    try:
        stmt = (
            select(QuestionBank, func.count(Question.id).label("question_count"))
            .outerjoin(Question, Question.bank_id == QuestionBank.id)
            .group_by(QuestionBank.id)
            .order_by(QuestionBank.created_at.desc())
        )
        result = await db.execute(stmt)
        rows = result.all()
    except Exception as e:
        print(f"[Banks API] DB offline/unreachable: {e}")
        return []
    for row in rows:
        if not row:
            continue
        bank = row[0]
        count = row[1] if len(row) > 1 else 0
        if hasattr(bank, "id"):
            banks_list.append({
                "id": str(bank.id),
                "name": getattr(bank, "name", ""),
                "description": getattr(bank, "description", None),
                "imocha_bank_id": getattr(bank, "imocha_bank_id", None),
                "question_count": count,
                "created_at": bank.created_at.isoformat() if getattr(bank, "created_at", None) else None,
            })

    return banks_list


@router.post("/banks", status_code=201)
async def create_bank(
    req: CreateBankRequest,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new question bank.
    """
    try:
        c_uuid = uuid.UUID(client_id)
    except ValueError:
        c_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")

    bank = QuestionBank(
        id=uuid.uuid4(),
        client_id=c_uuid,
        name=req.name.strip(),
        description=req.description,
        imocha_bank_id=req.imocha_bank_id,
        created_at=datetime.datetime.now(datetime.UTC),
    )
    db.add(bank)
    await db.commit()
    await db.refresh(bank)

    return {
        "id": str(bank.id),
        "name": bank.name,
        "description": bank.description,
        "imocha_bank_id": bank.imocha_bank_id,
        "created_at": bank.created_at.isoformat(),
    }


@router.post("/banks/{bank_id}/questions")
async def add_questions_to_bank(
    bank_id: str,
    req: AddQuestionsToBankRequest,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign multiple questions to a bank.
    """
    try:
        b_uuid = uuid.UUID(bank_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid bank_id format")

    # Verify bank exists
    b_res = await db.execute(select(QuestionBank).where(QuestionBank.id == b_uuid))
    if not b_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Question bank not found")

    q_uuids = []
    for qid in req.question_ids:
        try:
            q_uuids.append(uuid.UUID(qid))
        except ValueError:
            continue

    if not q_uuids:
        raise HTTPException(status_code=400, detail="No valid question_ids provided")

    now = datetime.datetime.now(datetime.UTC)
    stmt = (
        update(Question)
        .where(Question.id.in_(q_uuids))
        .values(bank_id=b_uuid, updated_at=now)
    )
    await db.execute(stmt)
    await db.commit()

    return {"bank_id": bank_id, "updated_questions": len(q_uuids)}
