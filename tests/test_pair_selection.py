"""Tests for image pair selection strategies."""

from pathlib import Path

import pytest

from app.services.pair_selection import (
    ImageCandidate,
    RandomPairSelector,
    build_candidates,
    get_pair_selector,
)


def test_random_pair_selector_returns_two_distinct_images() -> None:
    """The default selector should never return the same candidate twice."""
    selector = RandomPairSelector()
    images = [
        ImageCandidate(image_id="a.svg", path=Path("a.svg")),
        ImageCandidate(image_id="b.svg", path=Path("b.svg")),
    ]

    pair = selector.select_pair(images)

    assert pair.left.image_id != pair.right.image_id
    assert pair.strategy == "random"


def test_random_pair_selector_requires_two_images() -> None:
    """A comparison pair cannot be created from fewer than two images."""
    selector = RandomPairSelector()

    with pytest.raises(ValueError, match="At least two images"):
        selector.select_pair([ImageCandidate(image_id="a.svg", path=Path("a.svg"))])


def test_build_candidates_uses_root_relative_ids() -> None:
    """Candidate ids should be portable path strings relative to the image root."""
    image_root = Path("data/demo_images/cats")

    candidates = build_candidates([image_root / "cat-01-window.svg"], image_root)

    assert candidates[0].image_id == "cat-01-window.svg"


def test_get_pair_selector_rejects_unknown_strategy() -> None:
    """Unknown strategy names should fail loudly for now."""
    with pytest.raises(ValueError, match="Unknown pair selection strategy"):
        get_pair_selector("not-a-real-strategy")
