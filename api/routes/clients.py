from fastapi import APIRouter

router = APIRouter()


@router.get("/clients")
async def list_clients():
    # TODO Phase 2: return client list (admin only)
    return {"clients": [{"id": "00000000-0000-0000-0000-000000000001", "name": "Dev Client"}]}