"""Shared FastAPI dependencies."""
from fastapi import Request, HTTPException


async def get_client_id(request: Request) -> str:
    client_id = getattr(request.state, "client_id", None)
    if not client_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return client_id


async def get_db():
    from db.session import get_session
    async with get_session() as session:
        yield session