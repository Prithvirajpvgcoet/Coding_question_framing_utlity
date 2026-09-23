from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import generate, status, questions, feedback, clients
from api.middleware.auth import AuthMiddleware
from api.middleware.error_handler import register_exception_handlers

app = FastAPI(
    title="Multi-Agent Assessment API",
    version="0.1.0",
    description="Consolidated 7-Agent workflow for personalized coding assessment generation.",
    docs_url="/docs",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
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


@app.get("/health")
async def health():
    return {
        "status":  "ok",
        "phase":   0,
        "version": "0.1.0",
        "agents":  ["A", "B", "C", "D", "E", "F", "G"],
    }