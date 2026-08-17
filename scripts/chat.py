"""Interactive local test harness for the booking agent.

Talk to the agent as if you were a lead. Runs the REAL agent logic
(LLM decision, compliance gating, draft-vs-send, booking-link choice)
against a synthetic contact. No SMS is sent.

Usage:
    python -m scripts.chat
"""
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./dev.db")

from app.db import engine, SessionLocal
from app.models import Base, Contact, Enrollment
from app.agent import handle_inbound
from app.config import settings

Base.metadata.create_all(engine)   # ensure tables exist


def main():
    db = SessionLocal()

    name = input("Lead first name [Alex]: ").strip() or "Alex"
    company = input("Company for merge fields [Northgate]: ").strip() or "Northgate"

    # reuse existing test contact if it exists, create otherwise
    contact = db.query(Contact).filter_by(phone="+15550000001").first()
    if contact:
        contact.first_name = name
        contact.fields = {"company": company}
        contact.opted_out = False
        contact.status = "engaged"
        db.commit()
        print(f"(resuming existing thread for {name})")
    else:
        contact = Contact(
            phone="+15550000001",
            first_name=name,
            fields={"company": company},
            status="engaged",
            timezone="America/New_York",
        )
        db.add(contact)
        db.flush()
        db.add(Enrollment(
            contact_id=contact.id,
            sequence_id=1,
            current_step=0,
            status="paused",
        ))
        db.commit()

    print(f"\n--- Talking to the agent as {name}. Type 'quit' to exit. ---")
    print(f"    (AUTO_SEND={settings.auto_send}; booking={settings.booking_provider})\n")

    def show_new_outbound(since_id):
        rows = (
            db.query(__import__('app.models', fromlist=['Message']).Message)
            .filter_by(contact_id=contact.id, direction="out")
            .filter(__import__('app.models', fromlist=['Message']).Message.id > since_id)
            .order_by(__import__('app.models', fromlist=['Message']).Message.id)
            .all()
        )
        for m in rows:
            tag = "DRAFT" if m.status == "draft" else "SENT "
            print(f"  agent [{tag}]: {m.body}")
        db.refresh(contact)
        if contact.opted_out:
            print("  * contact opted out — agent will send nothing further")
        return rows[-1].id if rows else since_id

    last = 0
    while True:
        try:
            text = input(f"{name}: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text.lower() in ("quit", "exit", "q"):
            break
        if not text:
            continue
        handle_inbound(db, contact, text)
        last = show_new_outbound(last)
        if contact.opted_out:
            break

    print("\n--- session ended ---")
    db.close()


if __name__ == "__main__":
    main()
