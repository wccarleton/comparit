"""Run deployment preflight checks for comparit."""

from pathlib import Path

from app.core.config import get_settings
from app.db.connection import connect
from app.db.schema import initialize_schema
from app.services.image_indexer import discover_images


def check(condition: bool, message: str, errors: list[str]) -> None:
    """Record and print one preflight check result."""
    prefix = "OK" if condition else "FAIL"
    print(f"[{prefix}] {message}")
    if not condition:
        errors.append(message)


def can_write_directory(path: Path) -> bool:
    """Return whether a directory can be written to."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe_path = path / ".comparit-preflight.tmp"
        probe_path.write_text("ok", encoding="utf-8")
        probe_path.unlink()
    except OSError:
        return False
    return True


def main() -> int:
    """Run app-level readiness checks."""
    errors: list[str] = []
    settings = get_settings()

    check(bool(settings.app_name), "configuration loaded", errors)
    with connect() as connection:
        initialize_schema(connection)
    check(settings.resolved_database_path.exists(), "database initializes", errors)

    check(settings.resolved_image_root.exists(), "image root exists", errors)
    image_paths = discover_images(settings.resolved_image_root, settings.allowed_extensions)
    check(len(image_paths) >= 2, f"at least two images found ({len(image_paths)})", errors)

    check(settings.comparisons_per_session > 0, "comparisons_per_session is positive", errors)
    check(settings.token_validity_days > 0, "token_validity_days is positive", errors)
    check(
        settings.in_progress_expiry_minutes > 0,
        "in_progress_expiry_minutes is positive",
        errors,
    )
    check(
        can_write_directory(settings.resolved_export_output_dir),
        "export directory is writable",
        errors,
    )

    if errors:
        print(f"Preflight failed with {len(errors)} issue(s).")
        return 1

    print("Preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
