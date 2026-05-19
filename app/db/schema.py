"""SQLite schema scaffolding.

The schema is intentionally small but names the core domain concepts we expect
to implement later: images, participant tokens, comparison sessions, and
pairwise comparison responses.
"""

import sqlite3

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    relative_path TEXT NOT NULL UNIQUE,
    label TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- TODO: Add indexes once assignment/query patterns are finalized.
-- TODO: Consider migrations before public releases with existing deployments.
CREATE TABLE IF NOT EXISTS participant_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'unused' CHECK (
        status IN ('unused', 'in_progress', 'completed', 'revoked')
    ),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TEXT,
    completed_at TEXT,
    expires_at TEXT,
    consent_accepted_at TEXT,
    browser_session_id TEXT
);

CREATE TABLE IF NOT EXISTS comparison_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_id INTEGER,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    FOREIGN KEY (token_id) REFERENCES participant_tokens (id)
);

CREATE TABLE IF NOT EXISTS comparison_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_token_id INTEGER,
    browser_session_id TEXT NOT NULL,
    left_image_id TEXT NOT NULL,
    right_image_id TEXT NOT NULL,
    selected_image_id TEXT,
    action TEXT NOT NULL CHECK (action IN ('select', 'tie', 'skip')),
    pair_selection_strategy TEXT NOT NULL,
    response_time_ms INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (participant_token_id) REFERENCES participant_tokens (id)
);
"""


def initialize_schema(connection: sqlite3.Connection) -> None:
    """Create Phase 1 placeholder tables if they do not already exist."""
    connection.executescript(SCHEMA_SQL)
    _ensure_participant_token_schema(connection)
    _ensure_response_capture_schema(connection)
    _drop_orphaned_legacy_token_table(connection)
    connection.commit()


def _ensure_participant_token_schema(connection: sqlite3.Connection) -> None:
    """Migrate early token rows to the lightweight token-status schema."""
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(participant_tokens)").fetchall()
    }
    required_columns = {
        "id",
        "token",
        "status",
        "created_at",
        "started_at",
        "completed_at",
        "expires_at",
        "consent_accepted_at",
        "browser_session_id",
    }

    if required_columns.issubset(columns):
        return

    if "status" in columns:
        if "consent_accepted_at" not in columns:
            connection.execute("ALTER TABLE participant_tokens ADD COLUMN consent_accepted_at TEXT")
        if "browser_session_id" not in columns:
            connection.execute("ALTER TABLE participant_tokens ADD COLUMN browser_session_id TEXT")
        return

    connection.execute("ALTER TABLE participant_tokens RENAME TO participant_tokens_legacy")
    connection.executescript(
        """
        CREATE TABLE participant_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'unused' CHECK (
                status IN ('unused', 'in_progress', 'completed', 'revoked')
            ),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            started_at TEXT,
            completed_at TEXT,
            expires_at TEXT,
            consent_accepted_at TEXT,
            browser_session_id TEXT
        );
        """
    )

    if "status" in columns:
        connection.execute(
            """
            INSERT OR IGNORE INTO participant_tokens (
                id,
                token,
                status,
                created_at,
                started_at,
                completed_at,
                expires_at
            )
            SELECT id, token, status, created_at, started_at, completed_at, expires_at
            FROM participant_tokens_legacy
            """
        )
    else:
        connection.execute(
            """
            INSERT OR IGNORE INTO participant_tokens (id, token, status, created_at)
            SELECT
                id,
                token,
                CASE
                    WHEN is_active = 1 THEN 'unused'
                    ELSE 'revoked'
                END,
                created_at
            FROM participant_tokens_legacy
            """
        )

    connection.execute("DROP TABLE participant_tokens_legacy")


def _ensure_response_capture_schema(connection: sqlite3.Connection) -> None:
    """Migrate early Phase 1 response tables to the text-id capture schema.

    This project is still pre-release, so this intentionally stays small instead
    of introducing a migration framework. Once public users may have real data,
    migrations should become explicit and versioned.
    """
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(comparison_responses)").fetchall()
    }
    required_columns = {
        "browser_session_id",
        "participant_token_id",
        "left_image_id",
        "right_image_id",
        "selected_image_id",
        "action",
        "pair_selection_strategy",
        "response_time_ms",
        "created_at",
    }

    foreign_keys = connection.execute("PRAGMA foreign_key_list(comparison_responses)").fetchall()
    references_legacy_tokens = any(
        row["table"] == "participant_tokens_legacy" for row in foreign_keys
    )

    if required_columns.issubset(columns) and not references_legacy_tokens:
        return

    connection.execute("ALTER TABLE comparison_responses RENAME TO comparison_responses_legacy")
    connection.executescript(
        """
        CREATE TABLE comparison_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_token_id INTEGER,
            browser_session_id TEXT NOT NULL,
            left_image_id TEXT NOT NULL,
            right_image_id TEXT NOT NULL,
            selected_image_id TEXT,
            action TEXT NOT NULL CHECK (action IN ('select', 'tie', 'skip')),
            pair_selection_strategy TEXT NOT NULL,
            response_time_ms INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (participant_token_id) REFERENCES participant_tokens (id)
        );
        """
    )
    if required_columns.issubset(columns):
        connection.execute(
            """
            INSERT INTO comparison_responses (
                id,
                participant_token_id,
                browser_session_id,
                left_image_id,
                right_image_id,
                selected_image_id,
                action,
                pair_selection_strategy,
                response_time_ms,
                created_at
            )
            SELECT
                id,
                participant_token_id,
                browser_session_id,
                left_image_id,
                right_image_id,
                selected_image_id,
                action,
                pair_selection_strategy,
                response_time_ms,
                created_at
            FROM comparison_responses_legacy
            """
        )
    connection.execute("DROP TABLE comparison_responses_legacy")


def _drop_orphaned_legacy_token_table(connection: sqlite3.Connection) -> None:
    """Remove a leftover token migration table once no table references it."""
    table_exists = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'participant_tokens_legacy'
        """
    ).fetchone()
    if table_exists is None:
        return

    response_foreign_keys = connection.execute(
        "PRAGMA foreign_key_list(comparison_responses)"
    ).fetchall()
    if any(row["table"] == "participant_tokens_legacy" for row in response_foreign_keys):
        return

    connection.execute("DROP TABLE participant_tokens_legacy")
