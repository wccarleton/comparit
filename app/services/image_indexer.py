"""Image indexing scaffolding.

Future phases will persist discovered images and metadata. For Phase 1, this
module only discovers candidate files and reports what would be indexed.
"""

from pathlib import Path


def discover_images(image_root: Path, allowed_extensions: tuple[str, ...]) -> list[Path]:
    """Return image files below `image_root` with supported extensions."""
    # TODO: Persist discovered files and optional metadata in a future phase.
    if not image_root.exists():
        return []

    normalized_extensions = {extension.lower() for extension in allowed_extensions}
    return sorted(
        path
        for path in image_root.rglob("*")
        if path.is_file() and path.suffix.lower() in normalized_extensions
    )
