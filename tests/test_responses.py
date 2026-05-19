"""Tests for comparison response persistence."""

from app.db.responses import (
    ComparisonResponse,
    list_pair_keys_for_token,
    list_responses,
    record_response,
)
from app.db.tokens import create_tokens


def test_record_response_persists_choice(tmp_path) -> None:
    """A selected image response should be stored in SQLite."""
    database_path = tmp_path / "comparit.sqlite3"

    response_id = record_response(
        ComparisonResponse(
            participant_token_id=None,
            browser_session_id="browser-session-1",
            left_image_id="cat-01-window.svg",
            right_image_id="cat-02-books.svg",
            selected_image_id="cat-01-window.svg",
            action="select",
            pair_selection_strategy="random",
            response_time_ms=1234,
        ),
        database_path=database_path,
    )

    rows = list_responses(database_path=database_path)

    assert response_id == 1
    assert rows[0]["browser_session_id"] == "browser-session-1"
    assert rows[0]["selected_image_id"] == "cat-01-window.svg"
    assert rows[0]["action"] == "select"
    assert rows[0]["response_time_ms"] == 1234


def test_record_response_persists_skip_without_selected_image(tmp_path) -> None:
    """A skipped pair should be stored without a selected image id."""
    database_path = tmp_path / "comparit.sqlite3"

    record_response(
        ComparisonResponse(
            participant_token_id=None,
            browser_session_id="browser-session-1",
            left_image_id="cat-01-window.svg",
            right_image_id="cat-02-books.svg",
            selected_image_id=None,
            action="skip",
            pair_selection_strategy="random",
            response_time_ms=456,
        ),
        database_path=database_path,
    )

    rows = list_responses(database_path=database_path)

    assert rows[0]["selected_image_id"] is None
    assert rows[0]["action"] == "skip"


def test_list_pair_keys_for_token_returns_order_independent_keys(tmp_path) -> None:
    """Seen pairs should be normalized regardless of displayed side."""
    database_path = tmp_path / "comparit.sqlite3"
    token = create_tokens(["token-1"], validity_days=28, database_path=database_path)[0]

    record_response(
        ComparisonResponse(
            participant_token_id=token.id,
            browser_session_id="browser-session-1",
            left_image_id="cat-02-books.svg",
            right_image_id="cat-01-window.svg",
            selected_image_id="cat-01-window.svg",
            action="select",
            pair_selection_strategy="shuffle",
            response_time_ms=789,
        ),
        database_path=database_path,
    )

    assert list_pair_keys_for_token(token.id, database_path=database_path) == {
        ("cat-01-window.svg", "cat-02-books.svg")
    }
