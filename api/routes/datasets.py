"""
Dataset management API routes.
Enables uploading, seeding, inspecting, and deleting reference datasets
and domain scenarios used by Agent B for personalized question generation.
"""
import uuid
import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_client_id, get_db
from db.models import ReferenceDocument
from services.dataset_ingestion import ingest_file_content, load_seed_datasets

router = APIRouter()


class JsonDatasetRequest(BaseModel):
    items: List[Dict[str, Any]]
    doc_type: str = "DOMAIN_SCENARIO"
    domain: Optional[str] = None
    tags: List[str] = []


@router.get("/datasets")
async def list_datasets(
    topic: Optional[str] = None,
    doc_type: Optional[str] = None,
    domain: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """
    List reference documents and domain scenarios ingested for the client.
    """
    try:
        c_uuid = uuid.UUID(client_id)
    except ValueError:
        c_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")

    stmt = select(ReferenceDocument).where(ReferenceDocument.client_id == c_uuid)

    if topic:
        stmt = stmt.where(ReferenceDocument.topic.ilike(f"%{topic}%"))
    if doc_type:
        stmt = stmt.where(ReferenceDocument.doc_type == doc_type)
    if domain:
        stmt = stmt.where(ReferenceDocument.domain.ilike(f"%{domain}%"))

    stmt = stmt.order_by(ReferenceDocument.created_at.desc()).limit(limit).offset(offset)
    if db is not None:
        try:
            res = await db.execute(stmt)
            docs = res.scalars().all()
            # If the database is connected, return the user's stored documents (even if empty)
            return [
                {
                    "id": str(d.id),
                    "title": d.title,
                    "doc_type": d.doc_type,
                    "format": d.format,
                    "topic": d.topic,
                    "subtopic": d.subtopic,
                    "difficulty": d.difficulty,
                    "domain": d.domain,
                    "tags": d.tags,
                    "snippet": (d.raw_content[:200] + "...") if len(d.raw_content or "") > 200 else (d.raw_content or ""),
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                }
                for d in docs
            ]
        except Exception as e:
            print(f"[Datasets API] DB query failed ({e}), falling back to local seed datasets")

    # Fallback to local seed datasets
    seeds = await load_seed_datasets(None)
    items = []
    for idx, s in enumerate(seeds):
        items.append({
            "id": f"seed-offline-{idx}",
            "title": s.get("title", "Reference Problem"),
            "doc_type": "DOMAIN_SCENARIO",
            "format": "json",
            "topic": s.get("topic", "General"),
            "subtopic": s.get("subtopic", ""),
            "difficulty": s.get("difficulty", "MEDIUM"),
            "domain": s.get("domain", "Enterprise Domain"),
            "tags": s.get("tags", []),
            "snippet": s.get("scenario", "")[:200] + "..." if len(s.get("scenario", "")) > 200 else s.get("scenario", ""),
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
        })
    return items


@router.post("/datasets/upload", status_code=201)
async def upload_dataset_file(
    file: UploadFile = File(...),
    doc_type: str = Form("DOMAIN_SCENARIO"),
    tags: str = Form(""),
    custom_topic: Optional[str] = Form(None),
    custom_domain: Optional[str] = Form(None),
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload and ingest a reference dataset file (.pdf, .docx, .json, .csv, .md, .txt).
    Supports optional custom_topic and custom_domain overrides.
    """
    content_bytes = await file.read()
    extra_tags = [t.strip().lower() for t in tags.split(",") if t.strip()]

    try:
        saved_records = await ingest_file_content(
            db=db,
            client_id=client_id,
            filename=file.filename or "upload.txt",
            content_bytes=content_bytes,
            doc_type=doc_type,
            extra_tags=extra_tags,
            custom_topic=custom_topic,
            custom_domain=custom_domain,
        )
        return {
            "status": "INGESTED",
            "filename": file.filename,
            "count": len(saved_records),
            "records": saved_records,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to ingest file: {str(e)}")


@router.post("/datasets/json", status_code=201)
async def upload_json_dataset(
    req: JsonDatasetRequest,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Programmatically upload structured domain reference scenarios via JSON body.
    """
    try:
        c_uuid = uuid.UUID(client_id)
    except ValueError:
        c_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")

    now = datetime.datetime.now(datetime.UTC)
    saved = []

    for item in req.items:
        combined_tags = list(item.get("tags", [])) + req.tags
        combined_tags = list(dict.fromkeys(combined_tags))

        doc = ReferenceDocument(
            id=uuid.uuid4(),
            client_id=c_uuid,
            title=item.get("title", "Reference Item"),
            doc_type=item.get("doc_type", req.doc_type),
            format="json",
            topic=item.get("topic", "General"),
            subtopic=item.get("subtopic", ""),
            difficulty=item.get("difficulty", "MEDIUM"),
            domain=item.get("domain") or req.domain or "Enterprise Domain",
            tags=combined_tags,
            raw_content=item.get("scenario", "") or str(item),
            structured_data=item,
            created_at=now,
        )
        db.add(doc)
        saved.append(str(doc.id))

    await db.commit()
    return {"status": "INGESTED", "count": len(saved), "ids": saved}


@router.post("/datasets/seed", status_code=200)
async def seed_preloaded_datasets(
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Seeds out-of-the-box enterprise reference scenarios (FinTech, Logistics, Embedded, Core Algorithms).
    """
    seeds = await load_seed_datasets(db=db, client_id=client_id)
    return {
        "status": "SEEDED",
        "count": len(seeds),
        "message": f"Successfully loaded {len(seeds)} pre-seeded reference scenarios into knowledge base.",
    }


@router.get("/datasets/{dataset_id}")
async def get_dataset_detail(
    dataset_id: str,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        d_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset_id format")

    res = await db.execute(select(ReferenceDocument).where(ReferenceDocument.id == d_uuid))
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Reference document not found")

    return {
        "id": str(doc.id),
        "title": doc.title,
        "doc_type": doc.doc_type,
        "format": doc.format,
        "topic": doc.topic,
        "subtopic": doc.subtopic,
        "difficulty": doc.difficulty,
        "domain": doc.domain,
        "tags": doc.tags,
        "raw_content": doc.raw_content,
        "structured_data": doc.structured_data,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    # Handle offline seed datasets or non-persisted datasets gracefully
    if dataset_id.startswith("seed-offline-") or db is None:
        return {"status": "DELETED", "id": dataset_id, "note": "Removed from session view"}

    try:
        d_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset_id format")

    stmt = delete(ReferenceDocument).where(ReferenceDocument.id == d_uuid)
    res = await db.execute(stmt)
    await db.commit()

    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Reference document not found")

    return {"status": "DELETED", "id": dataset_id}
