"""Security middleware, validation, and hardening."""
import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import re

logger = logging.getLogger(__name__)

# Regex patterns for validation
PHONE_PATTERN = re.compile(r"^\+?1?\d{9,15}$")
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
URL_PATTERN = re.compile(r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}.*$")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (strict)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # Permissions policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Catch unhandled exceptions and return safe error responses."""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException:
            raise  # Let FastAPI handle HTTP exceptions
        except Exception as e:
            logger.exception(f"Unhandled exception on {request.method} {request.url.path}")
            # Don't leak internal details
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )


def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    if not phone or not isinstance(phone, str):
        return False
    return bool(PHONE_PATTERN.match(phone.strip()))


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_PATTERN.match(email.strip())) and len(email) <= 254


def validate_url(url: str) -> bool:
    """Validate URL format."""
    if not url or not isinstance(url, str):
        return False
    return bool(URL_PATTERN.match(url.strip())) and len(url) <= 2048


def sanitize_string(s: str, max_length: int = 1000) -> str:
    """Sanitize string input: strip, cap length, remove null bytes."""
    if not isinstance(s, str):
        return ""
    s = s.strip()[:max_length]
    # Remove null bytes
    s = s.replace("\x00", "")
    return s


def sanitize_json(data: dict, max_depth: int = 10) -> dict:
    """Sanitize JSON data: check depth, sanitize strings."""
    if max_depth <= 0:
        raise ValueError("JSON structure too deeply nested")

    if not isinstance(data, dict):
        return {}

    result = {}
    for key, value in data.items():
        # Sanitize key
        if not isinstance(key, str) or len(key) > 255:
            continue
        key = sanitize_string(key, 255)

        # Sanitize value
        if isinstance(value, str):
            result[key] = sanitize_string(value)
        elif isinstance(value, dict):
            result[key] = sanitize_json(value, max_depth - 1)
        elif isinstance(value, (int, float, bool)):
            result[key] = value
        elif isinstance(value, list):
            result[key] = [
                sanitize_string(v) if isinstance(v, str) else v
                for v in value[:100]  # Cap list length
            ]
        # Ignore other types (None, custom objects, etc.)

    return result


def is_suspicious_request(request: Request) -> bool:
    """Detect potentially malicious requests."""
    # Check for SQL injection patterns
    dangerous_patterns = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bSELECT\b.*\bFROM\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(--|#|\/\*|\*\/)",  # SQL comments
    ]

    path = request.url.path.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, path, re.IGNORECASE):
            logger.warning(f"Suspicious request pattern detected: {path}")
            return True

    return False
