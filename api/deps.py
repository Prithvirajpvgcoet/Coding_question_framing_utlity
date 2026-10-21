"""Shared FastAPI dependencies."""
from fastapi import Request, HTTPException

async def get_client_id(request: Request) -> str:
    client_id = getattr(request.state, "client_id", None)
    if not client_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return client_id

async def get_db(request: Request):
    from db.session import get_session, set_rls_client
    client_id = await get_client_id(request)
    session = None
    try:
        async with get_session() as s:
            session = s
            try:
                await set_rls_client(session, client_id)
            except Exception:
                pass
            yield session
    except HTTPException:
        # Route handler raised an HTTPException (e.g. 400/404); re-raise cleanly without corrupting the generator
        raise
    except Exception as db_err:
        # If the session failed to connect or query
        if session is None:
            yield None
        else:
            raise
