from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db
from app.models import Contact, Message, Booking

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    total = db.query(func.count(Contact.id)).scalar() or 0
    by_status = dict(
        db.query(Contact.status, func.count(Contact.id))
        .group_by(Contact.status).all()
    )
    booked = db.query(func.count(Booking.id)).scalar() or 0
    sent = db.query(func.count(Message.id)).filter(
        Message.direction == "out",
        Message.status.in_(["queued", "sent", "delivered"]),
    ).scalar() or 0
    delivered = db.query(func.count(Message.id)).filter(
        Message.status == "delivered"
    ).scalar() or 0
    return {
        "contacts": total,
        "by_status": by_status,
        "booked": booked,
        "sent": sent,
        "delivery_rate": round(delivered / sent, 3) if sent else None,
    }


@router.get("")
def list_contacts(status: str | None = Query(None), db: Session = Depends(get_db)):
    q = db.query(Contact)
    if status:
        q = q.filter(Contact.status == status)
    rows = q.order_by(Contact.created_at.desc()).limit(100).all()
    return [
        {
            "id": c.id, "name": c.first_name, "phone": c.phone,
            "status": c.status, "tags": (c.fields or {}).get("tags", []),
        }
        for c in rows
    ]


@router.get("/drafts")
def drafts(db: Session = Depends(get_db)):
    """Approval queue when AUTO_SEND=false."""
    rows = db.query(Message).filter_by(direction="out", status="draft").all()
    return [{"id": m.id, "contact_id": m.contact_id, "body": m.body} for m in rows]


@router.get("/{cid}/thread")
def thread(cid: int, db: Session = Depends(get_db)):
    msgs = (
        db.query(Message).filter_by(contact_id=cid)
        .order_by(Message.created_at).all()
    )
    return [
        {"direction": m.direction, "body": m.body,
         "status": m.status, "at": m.created_at.isoformat()}
        for m in msgs
    ]
