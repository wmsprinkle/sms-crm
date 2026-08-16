from datetime import datetime
from zoneinfo import ZoneInfo
from app.config import settings

STOP_WORDS = {"stop", "stopall", "unsubscribe", "cancel",
              "end", "quit", "optout", "opt-out"}


def is_stop(text: str) -> bool:
    return text.strip().lower().strip(".!") in STOP_WORDS


def in_quiet_hours(tz: str) -> bool:
    try:
        hour = datetime.now(ZoneInfo(tz)).hour
    except Exception:
        hour = datetime.utcnow().hour
    start, end = settings.quiet_hours_start, settings.quiet_hours_end
    return hour >= start or hour < end          # window wraps midnight


def can_send(contact) -> bool:
    if contact.opted_out:
        return False
    if in_quiet_hours(contact.timezone or "America/New_York"):
        return False
    return True
