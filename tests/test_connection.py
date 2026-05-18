"""Tests for SQLite connection tuning."""

from app.db.connection import connect


def test_sqlite_connection_uses_wal_and_busy_timeout(tmp_path) -> None:
    """The default SQLite settings should tolerate light concurrent access."""
    database_path = tmp_path / "comparit.sqlite3"

    with connect(database_path) as connection:
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        busy_timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]

    assert journal_mode == "wal"
    assert busy_timeout == 5000
