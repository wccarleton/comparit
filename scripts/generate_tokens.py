"""Generate participant invite tokens and ready-to-email links."""

import argparse
from urllib.parse import urlencode

from app.core.config import get_settings
from app.db.tokens import create_tokens
from app.services.tokens import generate_tokens

DEFAULT_TOKEN_COUNT = 10


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description="Generate participant invite links.")
    parser.add_argument("--count", type=int, default=DEFAULT_TOKEN_COUNT)
    return parser.parse_args()


def main() -> None:
    """Create tokens in SQLite and print participant links."""
    args = parse_args()
    settings = get_settings()
    token_values = generate_tokens(args.count)
    stored_tokens = create_tokens(token_values, validity_days=settings.token_validity_days)

    for participant_token in stored_tokens:
        query = urlencode({"t": participant_token.token})
        print(f"{settings.base_url}/?{query}")

    print(
        f"Generated {len(stored_tokens)} participant link(s); "
        f"tokens expire after {settings.token_validity_days} day(s)."
    )


if __name__ == "__main__":
    main()
