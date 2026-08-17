from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db
from app.models import Contact, Message, Booking, Enrollment, Sequence
from app.services import compliance
from app.services.telnyx_client import send_sms

router = APIRouter(prefix="/contacts", tags=["contacts"])


class ManualMessage(BaseModel):
    text: str


@router.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    total = db.query(func.count(Contact.id)).scalar() or 0
    by_status = dict(db.query(Contact.status, func.count(Contact.id)).group_by(Contact.status).all())
    booked = db.query(func.count(Booking.id)).filter(Booking.status == "booked").scalar() or 0
    in_sequence = db.query(func.count(Enrollment.id)).filter(Enrollment.status == "active").scalar() or 0
    replied = db.query(func.count(func.distinct(Message.contact_id))).filter(Message.direction == "in").scalar() or 0
    since = datetime.utcnow() - timedelta(hours=24)
    sent_24h = db.query(func.count(Message.id)).filter(
        Message.direction == "out", Message.created_at >= since,
        Message.status.in_(["queued", "sent", "delivered"]),
    ).scalar() or 0
    sent_total = db.query(func.count(Message.id)).filter(
        Message.direction == "out", Message.status.in_(["queued", "sent", "delivered"])
    ).scalar() or 0
    delivered = db.query(func.count(Message.id)).filter(Message.status == "delivered").scalar() or 0
    return {
        "contacts": total,
        "in_sequence": in_sequence,
        "replied": replied,
        "by_status": by_status,
        "booked": booked,
        "sent_24h": sent_24h,
        "sent": sent_total,
        "delivery_rate": round(delivered / sent_total, 3) if sent_total else None,
    }


@router.get("")
def list_contacts(status: str | None = Query(None), q: str | None = Query(None), db: Session = Depends(get_db)):
    query = db.query(Contact)
    if status:
        query = query.filter(Contact.status == status)
    if q:
        like = f"%{q}%"
        query = query.filter((Contact.first_name.ilike(like)) | (Contact.phone.ilike(like)))
    rows = query.order_by(Contact.created_at.desc()).limit(500).all()
    out = []
    for c in rows:
        last = db.query(Message).filter_by(contact_id=c.id).order_by(Message.created_at.desc()).first()
        enrollment = db.query(Enrollment).filter_by(contact_id=c.id).order_by(Enrollment.id.desc()).first()
        booking = db.query(Booking).filter_by(contact_id=c.id, status="booked").order_by(Booking.created_at.desc()).first()
        out.append({
            "id": c.id,
            "name": c.first_name,
            "phone": c.phone,
            "status": c.status,
            "tags": (c.fields or {}).get("tags", []),
            "fields": c.fields or {},
            "source": c.source,
            "timezone": c.timezone,
            "last_message": last.body if last else "",
            "last_message_at": last.created_at.isoformat() if last else None,
            "enrollment_status": enrollment.status if enrollment else None,
            "sequence_id": enrollment.sequence_id if enrollment else None,
            "booking_time": booking.scheduled_time.isoformat() if booking and booking.scheduled_time else None,
        })
    return out


@router.get("/drafts")
def drafts(db: Session = Depends(get_db)):
    rows = db.query(Message).filter_by(direction="out", status="draft").order_by(Message.created_at.desc()).all()
    result = []
    for m in rows:
        c = db.get(Contact, m.contact_id)
        result.append({
            "id": m.id,
            "contact_id": m.contact_id,
            "contact_name": c.first_name if c else None,
            "phone": c.phone if c else None,
            "body": m.body,
            "at": m.created_at.isoformat(),
        })
    return result


@router.get("/{cid}/thread")
def thread(cid: int, db: Session = Depends(get_db)):
    msgs = db.query(Message).filter_by(contact_id=cid).order_by(Message.created_at).all()
    return [{
        "id": m.id,
        "direction": m.direction,
        "body": m.body,
        "status": m.status,
        "telnyx_id": m.telnyx_id,
        "at": m.created_at.isoformat(),
    } for m in msgs]


@router.post("/{cid}/pause")
def pause(cid: int, db: Session = Depends(get_db)):
    contact = db.get(Contact, cid)
    if not contact:
        raise HTTPException(404, "contact not found")
    db.query(Enrollment).filter(Enrollment.contact_id == cid, Enrollment.status == "active").update(
        {"status": "paused"}, synchronize_session=False
    )
    db.commit()
    return {"ok": True, "status": "paused"}


@router.post("/{cid}/resume")
def resume(cid: int, db: Session = Depends(get_db)):
    contact = db.get(Contact, cid)
    if not contact:
        raise HTTPException(404, "contact not found")
    if contact.opted_out or contact.status == "booked":
        raise HTTPException(409, "booked or opted-out contacts cannot be resumed")
    db.query(Enrollment).filter(Enrollment.contact_id == cid, Enrollment.status == "paused").update(
        {"status": "active"}, synchronize_session=False
    )
    db.commit()
    return {"ok": True, "status": "active"}


@router.post("/{cid}/send")
def manual_send(cid: int, body: ManualMessage, db: Session = Depends(get_db)):
    contact = db.get(Contact, cid)
    if not contact:
        raise HTTPException(404, "contact not found")
    text = body.text.strip()[:1000]
    if not text:
        raise HTTPException(422, "empty message")
    if not compliance.can_send(contact):
        raise HTTPException(409, "blocked by compliance")
    data = send_sms(contact.phone, text)
    msg = Message(contact_id=cid, direction="out", body=text, telnyx_id=data.get("id"), status="queued")
    db.add(msg)
    db.commit()
    return {"ok": True, "id": msg.id, "status": msg.status}
