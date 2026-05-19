"""List participant tokens with operational status."""

from app.core.config import get_settings
from app.db.tokens import list_token_summaries


def main() -> None:
    """Print a compact token status table."""
    settings = get_settings()
    rows = list_token_summaries()
    print(f"Database: {settings.resolved_database_path}")
    if not rows:
        print("No participant tokens found.")
        return

    headers = [
        "id",
        "effective_status",
        "responses",
        "consent",
        "session",
        "created",
        "expires",
        "token",
    ]
    print("\t".join(headers))
    for row in rows:
        consent = "yes" if row["consent_accepted_at"] else "no"
        session = "bound" if row["browser_session_id"] else "none"
        values = [
            str(row["id"]),
            str(row["effective_status"]),
            str(row["response_count"]),
            consent,
            session,
            str(row["created_at"]),
            str(row["expires_at"] or ""),
            str(row["token"]),
        ]
        print("\t".join(values))


if __name__ == "__main__":
    main()
