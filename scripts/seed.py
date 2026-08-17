"""Seed a sample 4-step warm-lead re-engagement sequence.

Run once after setup:  python -m scripts.seed
Safe to re-run: skips if sequence already exists.
"""
from app.db import engine, SessionLocal
from app.models import Base, Sequence, Step

Base.metadata.create_all(engine)   # create tables if not already there

STEPS = [
    (0,     0, "Hi {{first_name}}, it's Relay from {{company}}. You'd looked into a "
               "walkthrough with us a little while back. Still worth a quick 20 min?"),
    (1,  2880, "Hey {{first_name}}, following up in case the timing was off before. "
               "Happy to work around your schedule. Want me to grab a slot?"),
    (2,  5760, "{{first_name}}, last nudge from me. If it's helpful I can send a link "
               "to pick any time that works. Just say the word."),
    (3, 10080, "No worries if now isn't right, {{first_name}}. I'll leave it here. "
               "Reply anytime and I'll get you booked."),
]


def run():
    db = SessionLocal()
    try:
        if db.query(Sequence).first():
            print("Sequence already exists, skipping seed.")
            return
        seq = Sequence(name="Q3 Warm Re-engagement", active=True)
        db.add(seq)
        db.flush()
        for order, delay, body in STEPS:
            db.add(Step(sequence_id=seq.id, order=order,
                        delay_minutes=delay, body=body))
        db.commit()
        print(f"Seeded sequence id={seq.id} with {len(STEPS)} steps")
    finally:
        db.close()


if __name__ == "__main__":
    run()
