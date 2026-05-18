"""Export captured comparison responses to CSV."""

import csv

from app.core.config import get_settings
from app.db.responses import list_responses

EXPORT_FILENAME = "comparison_responses.csv"


def main() -> None:
    """Write comparison responses to the configured export directory."""
    settings = get_settings()
    settings.resolved_export_output_dir.mkdir(parents=True, exist_ok=True)
    output_path = settings.resolved_export_output_dir / EXPORT_FILENAME
    responses = list_responses()

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
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(responses)

    print(f"Exported {len(responses)} response(s) to {output_path}.")


if __name__ == "__main__":
    main()
