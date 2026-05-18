"""Initialize the local SQLite database."""

from app.db.connection import connect
from app.db.schema import initialize_schema


def main() -> None:
    """Create the configured SQLite database and placeholder schema."""
    with connect() as connection:
        initialize_schema(connection)
    print("Database initialized.")


if __name__ == "__main__":
    main()
