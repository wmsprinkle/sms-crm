"""Approve or discard agent-drafted replies (used when AUTO_SEND=false)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Message, Contact
from app.services import compliance
from app.services.telnyx_client import send_sms

router = APIRouter(prefix="/drafts", tags=["drafts"])


@router.post("/{msg_id}/approve")
def approve(msg_id: int, db: Session = Depends(get_db)):
    msg = db.get(Message, msg_id)
    if not msg or msg.status != "draft":
        raise HTTPException(404, "draft not found")
    contact = db.get(Contact, msg.contact_id)
    if not compliance.can_send(contact):
        raise HTTPException(409, "blocked by compliance (opted out or quiet hours)")
    data = send_sms(contact.phone, msg.body)
    msg.telnyx_id = data.get("id")
    msg.status = "queued"
    db.commit()
    return {"ok": True, "telnyx_id": msg.telnyx_id}


@router.post("/{msg_id}/discard")
def discard(msg_id: int, db: Session = Depends(get_db)):
    msg = db.get(Message, msg_id)
    if not msg or msg.status != "draft":
        raise HTTPException(404, "draft not found")
    db.delete(msg)
    db.commit()
    return {"ok": True}
