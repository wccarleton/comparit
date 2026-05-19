"""Persistence helpers for participant invite tokens."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from app.db.connection import connect
from app.db.schema import initialize_schema

TokenStatus = Literal["unused", "in_progress", "completed", "revoked"]


@dataclass(frozen=True)
class ParticipantToken:
    """A participant invite token row."""

    id: int
    token: str
    status: TokenStatus
    created_at: str
    started_at: str | None
    completed_at: str | None
    expires_at: str | None
    consent_accepted_at: str | None
    browser_session_id: str | None


def utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(UTC)


def to_sqlite_timestamp(value: datetime) -> str:
    """Format a timezone-aware datetime for SQLite text storage."""
    return value.replace(microsecond=0).isoformat()


def create_tokens(
    tokens: list[str],
    validity_days: int = 28,
    database_path: Path | None = None,
) -> list[ParticipantToken]:
    """Store new participant tokens and return their rows."""
    if not tokens:
        return []

    expires_at = to_sqlite_timestamp(utc_now() + timedelta(days=validity_days))
    with connect(database_path) as connection:
        initialize_schema(connection)
        connection.executemany(
            "INSERT OR IGNORE INTO participant_tokens (token, expires_at) VALUES (?, ?)",
            [(token, expires_at) for token in tokens],
        )
        connection.commit()

        placeholders = ",".join("?" for _ in tokens)
        rows = connection.execute(
            f"""
            SELECT
                id,
                token,
                status,
                created_at,
                started_at,
                completed_at,
                expires_at,
                consent_accepted_at,
                browser_session_id
            FROM participant_tokens
            WHERE token IN ({placeholders})
            ORDER BY id
            """,
            tokens,
        ).fetchall()
    return [ParticipantToken(**dict(row)) for row in rows]


def get_token(token: str, database_path: Path | None = None) -> ParticipantToken | None:
    """Fetch one participant token by its opaque token string."""
    with connect(database_path) as connection:
        initialize_schema(connection)
        row = connection.execute(
            """
            SELECT
                id,
                token,
                status,
                created_at,
                started_at,
                completed_at,
                expires_at,
                consent_accepted_at,
                browser_session_id
            FROM participant_tokens
            WHERE token = ?
            """,
            (token,),
        ).fetchone()
    return ParticipantToken(**dict(row)) if row else None


def start_token(
    token: str,
    expiry_minutes: int,
    database_path: Path | None = None,
) -> ParticipantToken | None:
    """Mark an unused token as in progress and set a soft expiry."""
    now = utc_now()
    in_progress_expires_at = now + timedelta(minutes=expiry_minutes)

    with connect(database_path) as connection:
        initialize_schema(connection)
        row = connection.execute(
            "SELECT expires_at FROM participant_tokens WHERE token = ?",
            (token,),
        ).fetchone()
        existing_expires_at = (
            datetime.fromisoformat(row["expires_at"]) if row and row["expires_at"] else None
        )
        expires_at = min(
            [value for value in (existing_expires_at, in_progress_expires_at) if value is not None]
        )
        connection.execute(
            """
            UPDATE participant_tokens
            SET status = 'in_progress',
                started_at = COALESCE(started_at, ?),
                expires_at = ?
            WHERE token = ?
              AND status = 'unused'
            """,
            (to_sqlite_timestamp(now), to_sqlite_timestamp(expires_at), token),
        )
        connection.commit()
    return get_token(token, database_path=database_path)


def complete_token(token_id: int, database_path: Path | None = None) -> None:
    """Mark a token as completed."""
    with connect(database_path) as connection:
        initialize_schema(connection)
        connection.execute(
            """
            UPDATE participant_tokens
            SET status = 'completed',
                completed_at = COALESCE(completed_at, ?)
            WHERE id = ?
            """,
            (to_sqlite_timestamp(utc_now()), token_id),
        )
        connection.commit()


def revoke_token(token: str, database_path: Path | None = None) -> bool:
    """Mark a participant token as revoked by token string."""
    with connect(database_path) as connection:
        initialize_schema(connection)
        cursor = connection.execute(
            """
            UPDATE participant_tokens
            SET status = 'revoked'
            WHERE token = ?
              AND status != 'completed'
            """,
            (token,),
        )
        connection.commit()
        return cursor.rowcount > 0


def accept_consent(
    token_id: int,
    browser_session_id: str,
    database_path: Path | None = None,
) -> ParticipantToken | None:
    """Record consent acceptance and bind a token to a browser session."""
    with connect(database_path) as connection:
        initialize_schema(connection)
        connection.execute(
            """
            UPDATE participant_tokens
            SET consent_accepted_at = COALESCE(consent_accepted_at, ?),
                browser_session_id = COALESCE(browser_session_id, ?)
            WHERE id = ?
            """,
            (to_sqlite_timestamp(utc_now()), browser_session_id, token_id),
        )
        connection.commit()
        row = connection.execute(
            """
            SELECT
                id,
                token,
                status,
                created_at,
                started_at,
                completed_at,
                expires_at,
                consent_accepted_at,
                browser_session_id
            FROM participant_tokens
            WHERE id = ?
            """,
            (token_id,),
        ).fetchone()
    return ParticipantToken(**dict(row)) if row else None


def is_expired(token: ParticipantToken) -> bool:
    """Return whether a token has passed its expiry timestamp."""
    if not token.expires_at:
        return False
    expires_at = datetime.fromisoformat(token.expires_at)
    return expires_at <= utc_now()


def list_token_summaries(database_path: Path | None = None) -> list[dict[str, object]]:
    """Return participant tokens with response counts for operations/export."""
    with connect(database_path) as connection:
        initialize_schema(connection)
        rows = connection.execute(
            """
            SELECT
                participant_tokens.id,
                participant_tokens.token,
                participant_tokens.status,
                participant_tokens.created_at,
                participant_tokens.started_at,
                participant_tokens.completed_at,
                participant_tokens.expires_at,
                participant_tokens.consent_accepted_at,
                participant_tokens.browser_session_id,
                COUNT(comparison_responses.id) AS response_count
            FROM participant_tokens
            LEFT JOIN comparison_responses
                ON comparison_responses.participant_token_id = participant_tokens.id
            GROUP BY participant_tokens.id
            ORDER BY participant_tokens.id
            """
        ).fetchall()

    summaries = [dict(row) for row in rows]
    for summary in summaries:
        token = ParticipantToken(
            id=int(summary["id"]),
            token=str(summary["token"]),
            status=summary["status"],  # type: ignore[arg-type]
            created_at=str(summary["created_at"]),
            started_at=summary["started_at"],  # type: ignore[arg-type]
            completed_at=summary["completed_at"],  # type: ignore[arg-type]
            expires_at=summary["expires_at"],  # type: ignore[arg-type]
            consent_accepted_at=summary["consent_accepted_at"],  # type: ignore[arg-type]
            browser_session_id=summary["browser_session_id"],  # type: ignore[arg-type]
        )
        summary["is_expired"] = is_expired(token)
        summary["effective_status"] = "expired" if summary["is_expired"] else token.status
    return summaries


def reset_study_data(database_path: Path | None = None) -> None:
    """Delete participant tokens, sessions, and responses.

    Image files and local configuration are intentionally left untouched.
    """
    with connect(database_path) as connection:
        initialize_schema(connection)
        connection.execute("DELETE FROM comparison_responses")
        connection.execute("DELETE FROM comparison_sessions")
        connection.execute("DELETE FROM participant_tokens")
        connection.commit()
