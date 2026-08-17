from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.db import engine
from app.models import Base
from app.config import settings
from app.security import SecurityHeadersMiddleware, ErrorHandlingMiddleware
from app.routers import webhooks, imports, contacts, drafts, testchat
from app.worker.scheduler import start

app = FastAPI(
    title="SMS Booking CRM",
    description="Production SMS appointment setter",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Security middleware (apply first)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# CORS - restrict to localhost in dev, limit in prod
if settings.dry_run:
    origins = ["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:8000"]
else:
    origins = []  # Explicitly set in production via env var

if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        max_age=600,
    )

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Dev convenience. In production use Alembic migrations instead.
Base.metadata.create_all(engine)

app.include_router(webhooks.router)
app.include_router(imports.router)
app.include_router(contacts.router)
app.include_router(drafts.router)
app.include_router(testchat.router)

_CONSOLE = Path(__file__).parent / "static" / "console.html"


@app.get("/")
def console():
    """Serve the web console."""
    return FileResponse(_CONSOLE, media_type="text/html")


@app.on_event("startup")
def _startup():
    """Initialize scheduler on startup."""
    app.state.scheduler = start()


@app.get("/health")
def health():
    """Health check endpoint for monitoring and load balancers.

    Returns 200 if database is connected, 503 if not.
    """
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return {"ok": True, "dry_run": settings.dry_run}
    except Exception as e:
        return {"ok": False, "error": "database unavailable"}, 503
