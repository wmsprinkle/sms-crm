import csv
import io
from datetime import datetime
import phonenumbers
from app.models import Contact, Enrollment


def normalize(raw: str, region: str = "US") -> str | None:
    try:
        n = phonenumbers.parse(raw, region)
        if not phonenumbers.is_valid_number(n):
            return None
        return phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        return None


def import_csv(db, file_bytes: bytes, mapping: dict,
               sequence_id: int, source: str) -> dict:
    """Parse a CSV, create Contacts, and enroll each into a sequence.

    mapping maps our field -> the CSV column header, e.g.
        {"phone": "Phone", "first_name": "First", "company": "Company"}
    Any mapped field other than phone/first_name is stored in Contact.fields
    so it's available as a {{merge}} token.
    """
    reader = csv.DictReader(io.StringIO(file_bytes.decode("utf-8-sig")))
    imported = skipped = dupes = 0

    for row in reader:
        phone = normalize(row.get(mapping["phone"], ""))
        if not phone:
            skipped += 1
            continue
        if db.query(Contact).filter_by(phone=phone).first():
            dupes += 1
            continue

        fields = {
            key: row[col]
            for key, col in mapping.items()
            if key not in ("phone", "first_name") and col in row
        }
        contact = Contact(
            phone=phone,
            first_name=row.get(mapping.get("first_name", ""), None),
            fields=fields,
            source=source,
            status="active",
        )
        db.add(contact)
        db.flush()                                  # get contact.id
        db.add(Enrollment(
            contact_id=contact.id,
            sequence_id=sequence_id,
            current_step=0,
            status="active",
            next_send_at=datetime.utcnow(),          # first step fires on next tick
        ))
        imported += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "duplicates": dupes}
