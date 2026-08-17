from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.db import engine
from app.models import Base
from app.config import settings
from app.routers import webhooks, imports, contacts, drafts, testchat, sequences, runtime, activity
from app.worker.scheduler import start

app = FastAPI(title="Relay SMS Booking CRM")
Base.metadata.create_all(engine)

for router in (webhooks.router, imports.router, contacts.router, drafts.router,
               testchat.router, sequences.router, runtime.router, activity.router):
    app.include_router(router)

_CONSOLE = Path(__file__).parent / "static" / "console.html"

@app.get("/")
def console():
    return FileResponse(_CONSOLE)

@app.on_event("startup")
def _startup():
    app.state.scheduler = start()

@app.get("/health")
def health():
    return {"ok": True, "dry_run": settings.dry_run, "auto_send": settings.auto_send}
