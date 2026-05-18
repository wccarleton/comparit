"""Discover images that would be indexed in a future phase."""

from app.core.config import get_settings
from app.services.image_indexer import discover_images


def main() -> None:
    """Print a Phase 1 summary of discoverable image files."""
    settings = get_settings()
    images = discover_images(settings.resolved_image_root, settings.allowed_extensions)
    print(f"Found {len(images)} image(s) below {settings.resolved_image_root}.")
    print("TODO: Persist image records in the SQLite database in a future phase.")


if __name__ == "__main__":
    main()
