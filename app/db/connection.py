"""SQLite connection helpers.

Phase 1 keeps database access explicit and lightweight. A future phase can add
repository functions for image pairs, assignments, sessions, and exports.
"""

import sqlite3
from pathlib import Path

from app.core.config import get_settings


def connect(database_path: Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with row dictionaries enabled."""
    settings = get_settings()
    path = database_path or settings.resolved_database_path
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path, timeout=5.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection
