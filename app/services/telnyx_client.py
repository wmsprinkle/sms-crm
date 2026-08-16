import time
import uuid
import base64
import httpx
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from app.config import settings

API = "https://api.telnyx.com/v2/messages"


def send_sms(to: str, text: str) -> dict:
    """Send an SMS via Telnyx. Returns the message data (includes 'id').

    In DRY_RUN mode (the default for a fresh clone) nothing is sent to
    Telnyx: a fake id is returned and the caller logs the message as if it
    went out. Flip DRY_RUN=false once you have a registered number.
    """
    if settings.dry_run or not settings.telnyx_api_key:
        return {"id": f"dryrun-{uuid.uuid4().hex[:12]}", "dry_run": True}
    r = httpx.post(
        API,
        headers={"Authorization": f"Bearer {settings.telnyx_api_key}"},
        json={
            "from": settings.telnyx_from_number,
            "to": to,
            "text": text,
            "messaging_profile_id": settings.telnyx_messaging_profile_id,
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["data"]


def verify_webhook(raw_body: bytes, sig_header: str | None,
                   ts_header: str | None, tolerance: int = 300) -> bool:
    """Verify Telnyx Ed25519 signature over '{timestamp}|{raw_body}'.

    Rejects requests missing headers or older than `tolerance` seconds
    (replay protection). Public key comes from the portal: Keys &
    Credentials -> Public Key.
    """
    if not sig_header or not ts_header:
        return False
    try:
        if abs(time.time() - int(ts_header)) > tolerance:
            return False
        signed = f"{ts_header}|".encode() + raw_body
        key = VerifyKey(base64.b64decode(settings.telnyx_public_key))
        key.verify(signed, base64.b64decode(sig_header))
        return True
    except (BadSignatureError, ValueError, TypeError):
        return False
