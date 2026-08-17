from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Sequence, Step, Enrollment

router = APIRouter(prefix="/sequences", tags=["sequences"])


class StepIn(BaseModel):
    delay_minutes: int = 0
    body: str


class SequenceIn(BaseModel):
    name: str
    active: bool = True
    steps: list[StepIn]


def serialize(seq, db):
    active_count = db.query(Enrollment).filter_by(sequence_id=seq.id, status="active").count()
    return {
        "id": seq.id,
        "name": seq.name,
        "active": seq.active,
        "active_enrollments": active_count,
        "steps": [{"id": s.id, "order": s.order, "delay_minutes": s.delay_minutes, "body": s.body} for s in seq.steps],
    }


@router.get("")
def list_sequences(db: Session = Depends(get_db)):
    return [serialize(s, db) for s in db.query(Sequence).order_by(Sequence.id).all()]


@router.post("")
def create_sequence(body: SequenceIn, db: Session = Depends(get_db)):
    seq = Sequence(name=body.name.strip()[:120], active=body.active)
    db.add(seq); db.flush()
    for i, step in enumerate(body.steps):
        db.add(Step(sequence_id=seq.id, order=i, delay_minutes=max(0, step.delay_minutes), body=step.body[:1600]))
    db.commit(); db.refresh(seq)
    db.expire(seq, ["steps"])
    return serialize(seq, db)


@router.put("/{sid}")
def update_sequence(sid: int, body: SequenceIn, db: Session = Depends(get_db)):
    seq = db.get(Sequence, sid)
    if not seq:
        raise HTTPException(404, "sequence not found")
    seq.name = body.name.strip()[:120]
    seq.active = body.active
    db.query(Step).filter_by(sequence_id=sid).delete()
    for i, step in enumerate(body.steps):
        db.add(Step(sequence_id=sid, order=i, delay_minutes=max(0, step.delay_minutes), body=step.body[:1600]))
    db.commit(); db.refresh(seq)
    db.expire(seq, ["steps"])
    return serialize(seq, db)
