"""Drip worker: on each tick, send a rate-limited batch of due sequence
steps, gated by compliance. The batch cap + intra-batch spacing keep
throughput at/under your 10DLC campaign's messages-per-second limit, so a
queue of thousands drains steadily instead of firing all at once."""
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from app.config import settings
from app.db import SessionLocal
from app.models import Enrollment, Step, Contact, Message
from app.services import compliance
from app.services.merge import render
from app.services.telnyx_client import send_sms

INTERVAL = settings.worker_interval_seconds
# how many messages we're allowed to send per tick
BATCH = max(1, settings.send_rate_per_minute * INTERVAL // 60)
# seconds between sends within a tick, to smooth bursts into a steady rate
SPACING = INTERVAL / BATCH

# HARDCODED first message (no DB query, just merge tokens)
# This is the same for everyone, so no reason to query DB 10,000 times
FIRST_MESSAGE = "Hey {{first_name}}, I am reaching out to see if you were interested in term life or health insurance?"


def _advance(db, e: Enrollment):
    """Move an enrollment to its next step, or complete it."""
    nxt = (
        db.query(Step)
        .filter_by(sequence_id=e.sequence_id, order=e.current_step + 1)
        .first()
    )
    if nxt is not None:
        e.current_step += 1
        e.next_send_at = datetime.utcnow() + timedelta(minutes=nxt.delay_minutes)
    else:
        e.status = "completed"


def tick() -> None:
    db = SessionLocal()
    try:
        # oldest-due first, capped at the per-tick batch size
        due = (
            db.query(Enrollment)
            .filter(
                Enrollment.status == "active",
                Enrollment.next_send_at <= datetime.utcnow(),
            )
            .order_by(Enrollment.next_send_at)
            .limit(BATCH)
            .all()
        )
        for i, e in enumerate(due):
            contact = db.get(Contact, e.contact_id)
            if contact is None:
                e.status = "completed"
                db.commit()
                continue

            # compliance is the last gate before every send
            if not compliance.can_send(contact):
                e.next_send_at = datetime.utcnow() + timedelta(minutes=30)
                db.commit()
                continue

            # First message is hardcoded (same for everyone, skip DB query)
            if e.current_step == 0:
                body = render(FIRST_MESSAGE, contact)
            else:
                # Subsequent messages from database
                step = (
                    db.query(Step)
                    .filter_by(sequence_id=e.sequence_id, order=e.current_step)
                    .first()
                )
                if step is None:
                    e.status = "completed"
                    db.commit()
                    continue
                body = render(step.body, contact)
            try:
                data = send_sms(contact.phone, body)
                telnyx_id, status = data.get("id"), "queued"
            except Exception:
                telnyx_id, status = None, "failed"

            db.add(Message(contact_id=contact.id, direction="out", body=body,
                           telnyx_id=telnyx_id, status=status))
            _advance(db, e)
            db.commit()          # commit per send so a mid-batch crash is safe

            # space out sends within the tick (skip the wait after the last one)
            if i < len(due) - 1:
                time.sleep(SPACING)
    finally:
        db.close()


def start() -> BackgroundScheduler:
    s = BackgroundScheduler()
    # coalesce + max_instances=1 so overlapping/backed-up ticks don't stack
    s.add_job(tick, "interval", seconds=INTERVAL, id="drip",
              max_instances=1, coalesce=True)
    s.start()
    return s
