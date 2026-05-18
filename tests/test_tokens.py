"""Tests for participant token persistence."""

from app.db.responses import ComparisonResponse, count_responses_for_token, record_response
from app.db.tokens import (
    accept_consent,
    complete_token,
    create_tokens,
    get_token,
    is_expired,
    list_token_summaries,
    reset_study_data,
    start_token,
)


def test_create_and_start_token(tmp_path) -> None:
    """Generated tokens should be stored and movable into progress."""
    database_path = tmp_path / "comparit.sqlite3"

    stored = create_tokens(["token-1"], validity_days=28, database_path=database_path)
    started = start_token("token-1", expiry_minutes=30, database_path=database_path)

    assert stored[0].status == "unused"
    assert started is not None
    assert started.status == "in_progress"
    assert started.started_at is not None
    assert started.expires_at is not None


def test_complete_token(tmp_path) -> None:
    """Completed tokens should be marked with completed state."""
    database_path = tmp_path / "comparit.sqlite3"

    token = create_tokens(["token-1"], validity_days=28, database_path=database_path)[0]
    complete_token(token.id, database_path=database_path)
    completed = get_token("token-1", database_path=database_path)

    assert completed is not None
    assert completed.status == "completed"
    assert completed.completed_at is not None


def test_count_responses_for_token(tmp_path) -> None:
    """Response counts should be available for session completion."""
    database_path = tmp_path / "comparit.sqlite3"
    token = create_tokens(["token-1"], validity_days=28, database_path=database_path)[0]

    record_response(
        ComparisonResponse(
            participant_token_id=token.id,
            browser_session_id="browser-session-1",
            left_image_id="cat-01-window.svg",
            right_image_id="cat-02-books.svg",
            selected_image_id="cat-01-window.svg",
            action="select",
            pair_selection_strategy="random",
            response_time_ms=123,
        ),
        database_path=database_path,
    )

    assert count_responses_for_token(token.id, database_path=database_path) == 1


def test_create_tokens_sets_general_expiry(tmp_path) -> None:
    """Generated tokens should have a creation-time validity window."""
    database_path = tmp_path / "comparit.sqlite3"

    token = create_tokens(["token-1"], validity_days=-1, database_path=database_path)[0]

    assert token.expires_at is not None
    assert is_expired(token)


def test_accept_consent_records_timestamp(tmp_path) -> None:
    """Consent acceptance should be recorded on the participant token."""
    database_path = tmp_path / "comparit.sqlite3"
    token = create_tokens(["token-1"], validity_days=28, database_path=database_path)[0]

    accepted = accept_consent(token.id, database_path=database_path)

    assert accepted is not None
    assert accepted.consent_accepted_at is not None


def test_list_token_summaries_includes_response_count(tmp_path) -> None:
    """Token summaries should include counts and effective status."""
    database_path = tmp_path / "comparit.sqlite3"
    token = create_tokens(["token-1"], validity_days=28, database_path=database_path)[0]
    record_response(
        ComparisonResponse(
            participant_token_id=token.id,
            browser_session_id="browser-session-1",
            left_image_id="cat-01-window.svg",
            right_image_id="cat-02-books.svg",
            selected_image_id="cat-01-window.svg",
            action="select",
            pair_selection_strategy="random",
            response_time_ms=123,
        ),
        database_path=database_path,
    )

    summaries = list_token_summaries(database_path=database_path)

    assert summaries[0]["response_count"] == 1
    assert summaries[0]["effective_status"] == "unused"


def test_reset_study_data_removes_tokens_and_responses(tmp_path) -> None:
    """Reset should clear participant operational data."""
    database_path = tmp_path / "comparit.sqlite3"
    token = create_tokens(["token-1"], validity_days=28, database_path=database_path)[0]
    record_response(
        ComparisonResponse(
            participant_token_id=token.id,
            browser_session_id="browser-session-1",
            left_image_id="cat-01-window.svg",
            right_image_id="cat-02-books.svg",
            selected_image_id="cat-01-window.svg",
            action="select",
            pair_selection_strategy="random",
            response_time_ms=123,
        ),
        database_path=database_path,
    )

    reset_study_data(database_path=database_path)

    assert list_token_summaries(database_path=database_path) == []
    assert count_responses_for_token(token.id, database_path=database_path) == 0
