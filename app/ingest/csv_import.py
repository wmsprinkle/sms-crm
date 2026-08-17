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

    Returns:
        {"imported": N, "skipped": N, "duplicates": N, "errors": []}
    """
    if "phone" not in mapping:
        return {"error": "mapping must include 'phone' key", "imported": 0, "skipped": 0, "duplicates": 0}

    errors = []
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = file_bytes.decode("latin-1")
        except UnicodeDecodeError:
            return {"error": "could not decode file (try UTF-8 or Latin-1)", "imported": 0, "skipped": 0, "duplicates": 0}

    try:
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            return {"error": "CSV is empty or invalid", "imported": 0, "skipped": 0, "duplicates": 0}
    except csv.Error as e:
        return {"error": f"CSV parsing error: {str(e)}", "imported": 0, "skipped": 0, "duplicates": 0}

    imported = skipped = dupes = 0

    for row_num, row in enumerate(reader, start=2):  # start at 2 (after header)
        phone_col = mapping.get("phone")
        if not phone_col or phone_col not in row:
            errors.append(f"Row {row_num}: phone column '{phone_col}' not found")
            skipped += 1
            continue

        phone = normalize(row.get(phone_col, ""))
        if not phone:
            errors.append(f"Row {row_num}: invalid phone number '{row.get(phone_col, '')}'")
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
            first_name=(row.get(mapping.get("first_name", ""), "") or None)[:100],
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
    result = {"imported": imported, "skipped": skipped, "duplicates": dupes}
    if errors:
        result["errors"] = errors[:10]  # cap error list
    return result
