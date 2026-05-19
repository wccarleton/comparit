"""Export captured comparison responses and token metadata to CSV."""

import csv

from app.core.config import get_settings
from app.db.responses import list_responses
from app.db.tokens import list_token_summaries

RESPONSES_EXPORT_FILENAME = "comparison_responses.csv"
TOKENS_EXPORT_FILENAME = "participant_tokens.csv"


def main() -> None:
    """Write comparison responses and token summaries to the export directory."""
    settings = get_settings()
    settings.resolved_export_output_dir.mkdir(parents=True, exist_ok=True)
    responses_output_path = settings.resolved_export_output_dir / RESPONSES_EXPORT_FILENAME
    tokens_output_path = settings.resolved_export_output_dir / TOKENS_EXPORT_FILENAME
    responses = list_responses()
    token_summaries = list_token_summaries()

    fieldnames = [
        "id",
        "browser_session_id",
        "participant_token_id",
        "left_image_id",
        "right_image_id",
        "selected_image_id",
        "action",
        "pair_selection_strategy",
        "response_time_ms",
        "created_at",
    ]
    with responses_output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(responses)

    token_fieldnames = [
        "id",
        "token",
        "status",
        "effective_status",
        "is_expired",
        "created_at",
        "started_at",
        "completed_at",
        "expires_at",
        "consent_accepted_at",
        "browser_session_id",
        "response_count",
    ]
    with tokens_output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=token_fieldnames)
        writer.writeheader()
        writer.writerows(token_summaries)

    print(f"Exported {len(responses)} response(s) to {responses_output_path}.")
    print(f"Exported {len(token_summaries)} token row(s) to {tokens_output_path}.")


if __name__ == "__main__":
    main()
