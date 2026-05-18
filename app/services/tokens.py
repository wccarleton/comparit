"""Participant token scaffolding.

Tokens will eventually gate participant access and link responses to sessions.
For now, this module provides deterministic placeholders for the CLI script.
"""

from secrets import token_urlsafe


def generate_tokens(count: int) -> list[str]:
    """Generate opaque participant tokens."""
    # TODO: Store hashed or otherwise protected tokens if study requirements need it.
    if count < 1:
        raise ValueError("count must be at least 1")
    return [token_urlsafe(24) for _ in range(count)]
