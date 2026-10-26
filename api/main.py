import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import generate, status, questions, feedback, clients, dashboard, runs, banks, uploads, datasets
from api.middleware.auth import AuthMiddleware
from api.middleware.error_handler import register_exception_handlers

APP_VERSION = os.getenv("APP_VERSION", "0.1.0")

app = FastAPI(
    title="Multi-Agent Assessment API",
    version=APP_VERSION,
    description="Consolidated 7-Agent workflow for personalized coding assessment generation.",
    docs_url="/docs",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Read configurable origins from environment variable, falling back to standard local ports
configured_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
)
origins_list = [o.strip() for o in configured_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── Auth middleware ───────────────────────────────────────────────────────────
app.add_middleware(AuthMiddleware)

# ── Exception handlers ────────────────────────────────────────────────────────
register_exception_handlers(app)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(generate.router,  prefix="/api/v1")
app.include_router(status.router,    prefix="/api/v1")
app.include_router(questions.router, prefix="/api/v1")
app.include_router(feedback.router,  prefix="/api/v1")
app.include_router(clients.router,   prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(runs.router,      prefix="/api/v1")
app.include_router(banks.router,     prefix="/api/v1")
app.include_router(uploads.router,   prefix="/api/v1")
app.include_router(datasets.router,  prefix="/api/v1")


@app.get("/health")
async def health():
    return {
        "status":  "ok",
        "phase":   0,
        "version": APP_VERSION,
        "agents":  ["A", "B", "C", "D", "E", "F", "G"],
    }
