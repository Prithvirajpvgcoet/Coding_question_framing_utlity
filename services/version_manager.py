"""Create a new version snapshot whenever Agent F triggers a revision."""
import datetime
from sqlalchemy import insert
from db.session import get_session
from db.models import QuestionVersion

async def create_version(
    question_id:    str,
    version:        int,
    state_snapshot: dict,
    triggered_by:   str,
    re_entry_agent: str,
) -> None:
    print(f"[VersionManager] Creating version {version} for {question_id} | triggered_by={triggered_by}")
    async with get_session() as db:
        stmt = insert(QuestionVersion).values(
            question_id=question_id,
            version=version,
            state_snapshot=state_snapshot,
            triggered_by=triggered_by,
            re_entry_agent=re_entry_agent
        )
        await db.execute(stmt)
        await db.commit()
