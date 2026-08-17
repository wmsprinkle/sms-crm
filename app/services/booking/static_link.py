from app.config import settings


class StaticProvider:
    """A fixed link (Zoom scheduler, Google appt page, anything).

    Simple, but no closed loop: parse_webhook returns None, so the system
    won't automatically learn who booked unless that tool sends its own webhook.
    """

    def link_for(self, contact) -> str:
        return settings.static_booking_url

    def parse_webhook(self, headers: dict, body: bytes):
        return None
