from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse({"detail": "Missing X-API-Key header"}, status_code=401)

        # TODO Phase 2: verify api_key against clients table (bcrypt hash compare)
        # For Phase 0: accept any key and stub a client_id
        request.state.client_id = "00000000-0000-0000-0000-000000000001"
        return await call_next(request)