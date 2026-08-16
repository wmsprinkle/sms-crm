from app.config import settings
from .calendly import CalendlyProvider
from .static_link import StaticProvider


def get_provider():
    if settings.booking_provider == "calendly":
        return CalendlyProvider()
    return StaticProvider()
