"""Concurrency smoke tests for SQLite response writes."""

from concurrent.futures import ThreadPoolExecutor

from app.db.responses import ComparisonResponse, list_responses, record_response


def test_concurrent_response_inserts_complete(tmp_path) -> None:
    """Short response writes should succeed under modest threaded concurrency."""
    database_path = tmp_path / "comparit.sqlite3"
    insert_count = 32

    def insert_response(index: int) -> int:
        return record_response(
            ComparisonResponse(
                participant_token_id=None,
                browser_session_id=f"browser-session-{index}",
                left_image_id="cat-01-window.svg",
                right_image_id="cat-02-books.svg",
                selected_image_id="cat-01-window.svg",
                action="select",
                pair_selection_strategy="random",
                response_time_ms=index,
            ),
            database_path=database_path,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        response_ids = list(executor.map(insert_response, range(insert_count)))

    rows = list_responses(database_path=database_path)

    assert len(response_ids) == insert_count
    assert len(set(response_ids)) == insert_count
    assert len(rows) == insert_count
