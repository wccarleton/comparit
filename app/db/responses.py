"""Persistence helpers for comparison responses."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.db.connection import connect
from app.db.schema import initialize_schema

ResponseAction = Literal["select", "tie", "skip"]


@dataclass(frozen=True)
class ComparisonResponse:
    """A participant response to one displayed image pair."""

    participant_token_id: int | None
    browser_session_id: str
    left_image_id: str
    right_image_id: str
    selected_image_id: str | None
    action: ResponseAction
    pair_selection_strategy: str
    response_time_ms: int


def record_response(response: ComparisonResponse, database_path: Path | None = None) -> int:
    """Persist a comparison response and return its database id."""
    with connect(database_path) as connection:
        initialize_schema(connection)
        cursor = connection.execute(
            """
            INSERT INTO comparison_responses (
                browser_session_id,
                participant_token_id,
                left_image_id,
                right_image_id,
                selected_image_id,
                action,
                pair_selection_strategy,
                response_time_ms
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                response.browser_session_id,
                response.participant_token_id,
                response.left_image_id,
                response.right_image_id,
                response.selected_image_id,
                response.action,
                response.pair_selection_strategy,
                response.response_time_ms,
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)


def list_responses(database_path: Path | None = None) -> list[dict[str, object]]:
    """Return all captured responses in insertion order."""
    with connect(database_path) as connection:
        initialize_schema(connection)
        rows = connection.execute(
            """
            SELECT
                id,
                browser_session_id,
                participant_token_id,
                left_image_id,
                right_image_id,
                selected_image_id,
                action,
                pair_selection_strategy,
                response_time_ms,
                created_at
            FROM comparison_responses
            ORDER BY id
            """
        ).fetchall()
    return [dict(row) for row in rows]


def count_responses_for_token(token_id: int, database_path: Path | None = None) -> int:
    """Count captured responses for one participant token."""
    with connect(database_path) as connection:
        initialize_schema(connection)
        row = connection.execute(
            """
            SELECT COUNT(*) AS response_count
            FROM comparison_responses
            WHERE participant_token_id = ?
            """,
            (token_id,),
        ).fetchone()
    return int(row["response_count"])


def pair_key(left_image_id: str, right_image_id: str) -> tuple[str, str]:
    """Return an order-independent key for a displayed image pair."""
    return tuple(sorted((left_image_id, right_image_id)))


def list_pair_keys_for_token(
    token_id: int,
    database_path: Path | None = None,
) -> set[tuple[str, str]]:
    """Return order-independent pair keys already shown to one participant token."""
    with connect(database_path) as connection:
        initialize_schema(connection)
        rows = connection.execute(
            """
            SELECT left_image_id, right_image_id
            FROM comparison_responses
            WHERE participant_token_id = ?
            """,
            (token_id,),
        ).fetchall()
    return {pair_key(row["left_image_id"], row["right_image_id"]) for row in rows}
