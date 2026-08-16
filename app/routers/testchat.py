"""Test-chat endpoints: converse with the agent from the CRM console.

Only enabled while DRY_RUN=true — in live mode this surface is disabled so
nobody can puppet the agent from the web UI.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Contact, Enrollment, Message
from app.agent import handle_inbound
from app.config import settings

router = APIRouter(prefix="/testchat", tags=["testchat"])


def _guard():
    if not settings.dry_run:
        raise HTTPException(403, "test chat is disabled when DRY_RUN=false")


class NewLead(BaseModel):
    name: str = "Alex"
    company: str = "Northgate"


class Inbound(BaseModel):
    text: str


@router.post("/new")
def new_lead(body: NewLead, db: Session = Depends(get_db)):
    _guard()
    n = db.query(Contact).count()
    phone = f"+1555000{1000 + n:04d}"
    c = Contact(phone=phone, first_name=body.name[:40],
                fields={"company": body.company[:60]},
                status="engaged", timezone="America/New_York")
    db.add(c)
    db.flush()
    db.add(Enrollment(contact_id=c.id, sequence_id=1,
                      current_step=0, status="paused"))
    db.commit()
    return {"id": c.id, "name": c.first_name, "phone": c.phone}


@router.post("/{cid}/message")
def send_message(cid: int, body: Inbound, db: Session = Depends(get_db)):
    _guard()
    contact = db.get(Contact, cid)
    if not contact:
        raise HTTPException(404, "contact not found")
    text = body.text.strip()[:1000]        # cap inbound length
    if not text:
        raise HTTPException(422, "empty message")
    before = (db.query(Message.id).filter_by(contact_id=cid)
              .order_by(Message.id.desc()).first())
    last_id = before[0] if before else 0
    handle_inbound(db, contact, text)
    new = (db.query(Message).filter(Message.contact_id == cid,
                                    Message.id > last_id)
           .order_by(Message.id).all())
    return {
        "opted_out": contact.opted_out,
        "status": contact.status,
        "messages": [
            {"id": m.id, "direction": m.direction,
             "body": m.body, "status": m.status}
            for m in new
        ],
    }
