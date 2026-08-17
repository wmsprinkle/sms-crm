from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Optional


@dataclass
class BookingEvent:
    contact_ref: str            # value that maps back to a Contact (we use contact.id)
    scheduled_time: datetime
    event_uri: str
    status: str                 # "booked" | "canceled"


class BookingProvider(Protocol):
    def link_for(self, contact) -> str:
        """A scheduling URL to text this contact."""
        ...

    def parse_webhook(self, headers: dict, body: bytes) -> Optional[BookingEvent]:
        """Verify + parse a booking webhook. None if invalid or irrelevant."""
        ...
