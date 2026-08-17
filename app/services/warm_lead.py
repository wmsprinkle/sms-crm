"""Detect if an inbound message is from a warm lead (interested) or cold (uninterested).

This saves LLM tokens by only engaging AI on actual prospects.
Cold leads get auto-responded without AI involvement.
"""
import re

WARM_PATTERNS = [
    r"\b(yes|yeah|yep|sure|interested|tell me|learn|more|how|when|schedule|book|call|pricing|cost|available)\b",
    r"\b(sounds good|great|perfect|thanks|appreciate|really.*like)\b",
    r"\b(need|looking for|want to|can you help)\b",
]

COLD_PATTERNS = [
    r"\b(no|nope|not interested|unsubscribe|remove|stop|don't|dont|no thanks|nah|never)\b",
    r"\b(not now|busy|later|wrong number|not for me)\b",
    r"\b(spam|scam|who is|wtf|why)\b",
]


def is_warm_lead(text: str) -> bool:
    """Check if message indicates genuine interest.

    Returns True if message shows signs of interest.
    Returns False if clearly uninterested or irrelevant.
    """
    if not text or len(text) < 3:
        return False  # Too short, probably spam/error

    text_lower = text.lower().strip()

    # First check: hard NO signals (don't even check warm patterns)
    for pattern in COLD_PATTERNS:
        if re.search(pattern, text_lower):
            return False

    # Second check: positive signals
    for pattern in WARM_PATTERNS:
        if re.search(pattern, text_lower):
            return True

    # Ambiguous: very short responses might be warm (just "yes") or cold (just "no")
    # Treat as warm if more than 1 word (likely genuine response)
    word_count = len(text_lower.split())
    return word_count > 1


def get_cold_response(first_name: str) -> str:
    """Auto-response for cold/uninterested leads (no AI).

    Quick, friendly response that doesn't waste LLM tokens.
    """
    return f"Got it, {first_name}. No problem—feel free to reach out if your situation changes. Thanks!"
