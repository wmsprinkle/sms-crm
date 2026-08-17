from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.db import engine
from app.models import Base, Contact
from app.config import settings
from app.routers import webhooks, imports, contacts, drafts, testchat
from app.worker.scheduler import start, FIRST_MESSAGE
from app.services.merge import render
from app.services.telnyx_client import send_sms

app = FastAPI(title="SMS Booking CRM")

# Dev convenience. In production use Alembic migrations instead.
Base.metadata.create_all(engine)

app.include_router(webhooks.router)
app.include_router(imports.router)
app.include_router(contacts.router)
app.include_router(drafts.router)
app.include_router(testchat.router)

_CONSOLE = Path(__file__).parent / "static" / "console.html"


class SendTestSMS(BaseModel):
    phone: str


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


@app.post("/test/send-sms")
def test_send_sms(body: SendTestSMS):
    """Test endpoint: send the first message to a phone number.

    Used to test outbound SMS and trigger inbound webhook flow.
    """
    import httpx

    phone = body.phone.strip()
    fake_contact = Contact(phone=phone, first_name="Friend")
    rendered = render(FIRST_MESSAGE, fake_contact)

    try:
        data = send_sms(phone, rendered)
        return {
            "sent": True,
            "phone": phone,
            "message": rendered,
            "telnyx_id": data.get("id")
        }
    except httpx.HTTPError as e:
        return {
            "error": f"HTTP {e.response.status_code if hasattr(e, 'response') else 'unknown'}",
            "detail": e.response.text if hasattr(e, 'response') else str(e)
        }, 500
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}, 500
