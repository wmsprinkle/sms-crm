"""The conversational booking agent: decides the next move on an inbound text
and either sends it or holds it as a draft, gated by compliance.

Smart token usage: AI only engages on warm leads (interested prospects).
Cold/uninterested responses get auto-responded without LLM."""
from app.models import Contact, Message, Enrollment
from app.services import compliance
from app.services.llm import decide
from app.services.warm_lead import is_warm_lead, get_cold_response
from app.services.telnyx_client import send_sms
from app.services.booking import get_provider
from app.config import settings


def _halt(db, contact_id: int, new_status: str):
    """Halt every non-terminal enrollment for a contact (active or paused)."""
    db.query(Enrollment).filter(
        Enrollment.contact_id == contact_id,
        Enrollment.status.in_(["active", "paused"]),
    ).update({"status": new_status}, synchronize_session=False)


def handle_inbound(db, contact: Contact, text: str) -> None:
    db.add(Message(contact_id=contact.id, direction="in", body=text))

    # 1) hard STOP wins before any model call
    if compliance.is_stop(text):
        contact.opted_out = True
        contact.status = "opted_out"
        _halt(db, contact.id, "opted_out")
        db.commit()
        return

    # 2) pause drips so a scheduled nudge can't fire mid-conversation
    db.query(Enrollment).filter_by(contact_id=contact.id, status="active").update(
        {"status": "paused"}, synchronize_session=False
    )
    contact.status = "engaged"

    # 3) check if this is a warm lead (interested) before wasting LLM tokens
    if not is_warm_lead(text):
        # Cold lead: auto-respond without AI
        msg = get_cold_response(contact.first_name or "there")
        if settings.auto_send and compliance.can_send(contact):
            data = send_sms(contact.phone, msg)
            db.add(Message(contact_id=contact.id, direction="out", body=msg,
                           telnyx_id=data.get("id"), status="queued"))
        else:
            db.add(Message(contact_id=contact.id, direction="out", body=msg,
                           status="draft"))
        db.commit()
        return

    # 4) warm lead: let the agent decide the next move (use LLM)
    link = get_provider().link_for(contact)
    thread = (
        db.query(Message)
        .filter_by(contact_id=contact.id)
        .order_by(Message.created_at)
        .all()
    )
    d = decide(contact, thread, link)

    if d["action"] == "opt_out":
        contact.opted_out = True
        contact.status = "opted_out"
        db.commit()
        return

    msg = (d.get("message") or "").strip()
    if d["action"] == "wait" or not msg:
        db.commit()
        return

    # 5) send now, or hold as a draft for approval (AUTO_SEND leash)
    if settings.auto_send and compliance.can_send(contact):
        data = send_sms(contact.phone, msg)
        db.add(Message(contact_id=contact.id, direction="out", body=msg,
                       telnyx_id=data.get("id"), status="queued"))
    else:
        db.add(Message(contact_id=contact.id, direction="out", body=msg,
                       status="draft"))
    db.commit()
