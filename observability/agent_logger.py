"""
Fire-and-forget helper that persists agent run metadata to the agent_runs table.

Every call to groq_chat() returns a `usage` dict with:
    input_tokens, output_tokens, latency_ms, model, prompt_hash, cost_usd

Call log_agent_run() at the end of each agent runner to build the audit trail.
Never raises — errors are swallowed with a warning so agents are never blocked.
"""
import datetime
import logging
import uuid
from typing import Optional

log = logging.getLogger(__name__)


async def log_agent_run(
    question_id: str,
    request_id: str,
    agent_name: str,
    usage: dict,
    status: str = "SUCCESS",
    retry_count: int = 0,
    internal_step: bool = False,
    error_detail: Optional[str] = None,
) -> None:
    """Insert one row into agent_runs. Silently swallows all exceptions."""
    try:
        from db.session import get_session
        from db.models import AgentRun

        async with get_session() as db:
            run = AgentRun(
                id=uuid.uuid4(),
                request_id=_to_uuid(request_id),
                question_id=_to_uuid(question_id),
                agent_name=agent_name,
                model=usage.get("model", "unknown"),
                prompt_hash=usage.get("prompt_hash"),
                input_tokens=usage.get("input_tokens"),
                output_tokens=usage.get("output_tokens"),
                cost_usd=usage.get("cost_usd"),
                latency_ms=usage.get("latency_ms"),
                status=status,
                retry_count=retry_count,
                internal_step=internal_step,
                error_detail=error_detail,
                created_at=datetime.datetime.now(datetime.UTC),
            )
            db.add(run)
            await db.commit()
    except Exception as exc:
        log.warning(f"[AgentLogger] Failed to log run for {agent_name}: {exc}")


def _to_uuid(value: str) -> Optional[uuid.UUID]:
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError):
        return None
