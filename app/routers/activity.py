import asyncio, json
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db import get_db, SessionLocal
from app.models import Message, Contact, Booking

router = APIRouter(tags=["activity"])


def recent_activity(db: Session, limit=50):
    events = []
    msgs = db.query(Message).order_by(Message.created_at.desc()).limit(limit).all()
    for m in msgs:
        c = db.get(Contact, m.contact_id)
        kind = "reply" if m.direction == "in" else "send"
        if m.status == "draft": kind = "draft"
        events.append({
            "kind": kind, "id": f"m{m.id}", "contact_id": m.contact_id,
            "name": c.first_name if c else None, "phone": c.phone if c else None,
            "body": m.body, "status": m.status, "at": m.created_at.isoformat(),
        })
    books = db.query(Booking).order_by(Booking.created_at.desc()).limit(limit).all()
    for b in books:
        c = db.get(Contact, b.contact_id)
        events.append({
            "kind": "book", "id": f"b{b.id}", "contact_id": b.contact_id,
            "name": c.first_name if c else None, "phone": c.phone if c else None,
            "body": b.scheduled_time.isoformat() if b.scheduled_time else "Booked",
            "status": b.status, "at": b.created_at.isoformat(),
        })
    events.sort(key=lambda e: e["at"], reverse=True)
    return events[:limit]


@router.get("/activity")
def activity(db: Session = Depends(get_db)):
    return recent_activity(db)


@router.get("/events")
async def events():
    async def stream():
        last = None
        while True:
            db = SessionLocal()
            try:
                rows = recent_activity(db, limit=15)
                signature = tuple((r["id"], r["status"]) for r in rows)
                if signature != last:
                    last = signature
                    yield f"data: {json.dumps({'type':'refresh','at':datetime.utcnow().isoformat()})}\n\n"
                else:
                    yield ": keepalive\n\n"
            finally:
                db.close()
            await asyncio.sleep(2)
    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control":"no-cache"})
