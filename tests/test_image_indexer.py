"""Tests for Phase 1 image discovery scaffolding."""

from pathlib import Path

from app.services.image_indexer import discover_images


def test_discover_images_finds_demo_svg_files() -> None:
    """The bundled demo image library should be indexable out of the box."""
    demo_root = Path("data/demo_images/cats")

    images = discover_images(demo_root, (".svg",))

    assert len(images) == 6
    assert images[0].name == "cat-01-window.svg"
