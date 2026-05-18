"""Clear local participant tokens and response data."""

import argparse

from app.db.tokens import reset_study_data


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(
        description="Delete participant tokens, sessions, and responses."
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Actually perform the reset.",
    )
    return parser.parse_args()


def main() -> int:
    """Reset study data only after an explicit confirmation flag."""
    args = parse_args()
    if not args.yes:
        print("Refusing to reset study data without --yes.")
        print("Run: python scripts/reset_study_data.py --yes")
        return 1

    reset_study_data()
    print("Deleted participant tokens, sessions, and responses.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
