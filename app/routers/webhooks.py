from fastapi import APIRouter, Request, HTTPException
from app.db import SessionLocal
from app.models import Contact, Message, Enrollment, Booking
from app.services.telnyx_client import verify_webhook
from app.services.booking import get_provider
from app.agent import handle_inbound

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/telnyx")
async def telnyx(request: Request):
    raw = await request.body()
    if not verify_webhook(
        raw,
        request.headers.get("telnyx-signature-ed25519"),
        request.headers.get("telnyx-timestamp"),
    ):
        raise HTTPException(status_code=403, detail="bad signature")

    event = (await request.json())["data"]
    etype = event["event_type"]
    payload = event["payload"]

    # delivery receipts -> update the stored message status by telnyx id
    if etype in ("message.sent", "message.finalized"):
        db = SessionLocal()
        try:
            msg = db.query(Message).filter_by(telnyx_id=payload["id"]).first()
            if msg and payload.get("to"):
                msg.status = payload["to"][0]["status"]
                db.commit()
        finally:
            db.close()
        return {"ok": True}

    if etype != "message.received":
        return {"ok": True}

    phone = payload["from"]["phone_number"]
    text = payload.get("text", "")

    db = SessionLocal()
    try:
        # idempotency: skip if we've already logged this telnyx message id
        if db.query(Message).filter_by(telnyx_id=payload["id"]).first():
            return {"ok": True}

        contact = db.query(Contact).filter_by(phone=phone).first()
        if contact is None:
            contact = Contact(phone=phone, status="engaged")
            db.add(contact)
            db.flush()
        handle_inbound(db, contact, text, telnyx_id=payload["id"])
    finally:
        db.close()
    return {"ok": True}


@router.post("/booking")
async def booking(request: Request):
    raw = await request.body()
    event = get_provider().parse_webhook(dict(request.headers), raw)
    if event is None or not event.contact_ref:
        return {"ok": True}

    db = SessionLocal()
    try:
        contact = db.get(Contact, int(event.contact_ref))
        if contact:
            db.add(Booking(
                contact_id=contact.id,
                provider="calendly",
                event_uri=event.event_uri,
                scheduled_time=event.scheduled_time,
                status=event.status,
            ))
            contact.status = "booked"
            db.query(Enrollment).filter_by(contact_id=contact.id).filter(
                Enrollment.status.in_(["active", "paused"])
            ).update({"status": "booked"}, synchronize_session=False)
            db.commit()
    finally:
        db.close()
    return {"ok": True}
