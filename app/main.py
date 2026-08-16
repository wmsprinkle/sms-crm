from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.db import engine
from app.models import Base
from app.config import settings
from app.routers import webhooks, imports, contacts, drafts, testchat
from app.worker.scheduler import start

app = FastAPI(title="SMS Booking CRM")

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
    return FileResponse(_CONSOLE)


@app.on_event("startup")
def _startup():
    app.state.scheduler = start()


@app.get("/health")
def health():
    return {"ok": True, "dry_run": settings.dry_run}
