import json
from datetime import datetime
import httpx
from app.config import settings
from app.services.booking.base import BookingEvent


class CalendlyProvider:
    """Single-use link per contact + invitee.created webhook to close the loop."""

    def link_for(self, contact) -> str:
        r = httpx.post(
            "https://api.calendly.com/scheduling_links",
            headers={"Authorization": f"Bearer {settings.calendly_token}"},
            json={
                "max_event_count": 1,
                "owner": settings.calendly_event_type_uri,
                "owner_type": "EventType",
            },
            timeout=15,
        )
        r.raise_for_status()
        url = r.json()["resource"]["booking_url"]
        # round-trip the contact id so the booking webhook can match back
        return f"{url}?utm_content={contact.id}"

    def parse_webhook(self, headers: dict, body: bytes):
        # For production, verify the Calendly-Webhook-Signature header here
        # using settings.calendly_signing_key before trusting the payload.
        payload = json.loads(body)
        if payload.get("event") != "invitee.created":
            return None
        p = payload["payload"]
        ref = (p.get("tracking") or {}).get("utm_content", "")
        start = p["scheduled_event"]["start_time"].replace("Z", "+00:00")
        return BookingEvent(
            contact_ref=ref,
            scheduled_time=datetime.fromisoformat(start),
            event_uri=p["scheduled_event"]["uri"],
            status="booked",
        )
