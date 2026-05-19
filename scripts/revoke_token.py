"""Revoke a participant token."""

import argparse

from app.db.tokens import revoke_token


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description="Revoke one participant token.")
    parser.add_argument("token", help="Opaque participant token string to revoke.")
    return parser.parse_args()


def main() -> int:
    """Revoke the requested token."""
    args = parse_args()
    revoked = revoke_token(args.token)
    if not revoked:
        print("Token was not revoked. It may not exist, or it may already be completed.")
        return 1

    print("Token revoked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
