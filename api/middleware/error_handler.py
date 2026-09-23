from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

log = structlog.get_logger()


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception):
        log.error("unhandled_exception", path=request.url.path, error=str(exc))
        return JSONResponse({"detail": "Internal server error"}, status_code=500)