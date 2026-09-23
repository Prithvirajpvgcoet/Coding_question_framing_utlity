"""Create a new version snapshot whenever Agent F triggers a revision."""
import datetime


async def create_version(
    question_id:    str,
    version:        int,
    state_snapshot: dict,
    triggered_by:   str,
    re_entry_agent: str,
) -> None:
    # TODO Phase 6: insert into question_versions table
    print(f"[VersionManager] Creating version {version} for {question_id} | triggered_by={triggered_by}")