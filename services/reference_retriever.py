"""
Reference Retriever Service: Performs hybrid matching (topic, subtopic, difficulty, domain)
against ingested datasets to supply Agent B with personalized context for Agent C.
"""
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ReferenceDocument
from services.dataset_ingestion import load_seed_datasets


def _score_item(item: Dict[str, Any], topic: str, subtopic: str, difficulty: str) -> int:
    """Computes a relevance score between an item and the requirements."""
    score = 0
    item_topic = str(item.get("topic", "")).lower()
    item_subtopic = str(item.get("subtopic", "")).lower()
    item_diff = str(item.get("difficulty", "")).upper()
    item_tags = [str(t).lower() for t in item.get("tags", [])]

    req_topic = topic.lower()
    req_subtopic = subtopic.lower()
    req_diff = difficulty.upper()

    # Topic match
    if req_topic and (req_topic in item_topic or item_topic in req_topic):
        score += 10
    elif any(req_topic in t for t in item_tags):
        score += 8

    # Subtopic match
    if req_subtopic:
        if req_subtopic in item_subtopic or item_subtopic in req_subtopic:
            score += 6
        elif any(req_subtopic in t for t in item_tags):
            score += 5

    # Difficulty match
    if req_diff and req_diff == item_diff:
        score += 3

    return score


async def retrieve_references(
    requirements: Dict[str, Any],
    client_id: str,
    limit: int = 3,
    db: Optional[AsyncSession] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves the most relevant reference problems and domain scenarios
    for the requested question generation parameters.
    """
    topic = requirements.get("topic", "")
    subtopic = requirements.get("subtopic", "")
    difficulty = requirements.get("difficulty", "MEDIUM")

    retrieved: List[Dict[str, Any]] = []

    # 1. Try querying database if DB session is active
    if db is not None:
        try:
            try:
                c_uuid = uuid.UUID(client_id)
            except ValueError:
                c_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")

            stmt = (
                select(ReferenceDocument)
                .where(
                    ReferenceDocument.client_id == c_uuid,
                    or_(
                        func.lower(ReferenceDocument.topic) == topic.lower(),
                        func.lower(ReferenceDocument.subtopic) == subtopic.lower(),
                        ReferenceDocument.tags.contains([topic.lower()]),
                    )
                )
                .limit(limit * 2)
            )
            res = await db.execute(stmt)
            docs = res.scalars().all()

            for doc in docs:
                data = doc.structured_data or {}
                retrieved.append({
                    "id": str(doc.id),
                    "title": doc.title,
                    "domain": doc.domain or data.get("domain", "Enterprise Domain"),
                    "topic": doc.topic,
                    "subtopic": doc.subtopic,
                    "difficulty": doc.difficulty,
                    "scenario": doc.raw_content or data.get("scenario", ""),
                    "algorithmic_pattern": data.get("algorithmic_pattern", ""),
                    "sample_constraints": data.get("sample_constraints", []),
                })
        except Exception as e:
            print(f"[Reference Retriever] DB query fallback: {e}")

    # 2. Fallback to pre-seeded local dataset if DB produced fewer than limit items
    if len(retrieved) < limit:
        seed_items = await load_seed_datasets()
        # Score and rank seed items
        scored_seeds = []
        for item in seed_items:
            # Avoid duplicate titles if already retrieved from DB
            if any(r.get("title") == item.get("title") for r in retrieved):
                continue
            s = _score_item(item, topic, subtopic, difficulty)
            scored_seeds.append((s, item))

        scored_seeds.sort(key=lambda x: x[0], reverse=True)

        needed = limit - len(retrieved)
        for _, seed in scored_seeds[:needed]:
            retrieved.append({
                "title": seed.get("title"),
                "domain": seed.get("domain", "General Enterprise"),
                "topic": seed.get("topic"),
                "subtopic": seed.get("subtopic"),
                "difficulty": seed.get("difficulty"),
                "scenario": seed.get("scenario"),
                "algorithmic_pattern": seed.get("algorithmic_pattern"),
                "sample_constraints": seed.get("sample_constraints", []),
            })

    return retrieved[:limit]
