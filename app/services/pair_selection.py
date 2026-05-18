"""Image pair selection strategies.

This module is intentionally small but public within the app architecture. Study
owners should eventually be able to replace the default random strategy with a
balanced design, active-learning sampler, seeded replay, or a custom plugin.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from random import SystemRandom
from typing import Protocol


@dataclass(frozen=True)
class ImageCandidate:
    """An image that can appear in a pairwise comparison."""

    image_id: str
    path: Path


@dataclass(frozen=True)
class ImagePair:
    """Two images selected for a comparison trial."""

    left: ImageCandidate
    right: ImageCandidate
    strategy: str


class PairSelector(Protocol):
    """Interface for selecting the next image pair."""

    strategy_name: str

    def select_pair(self, images: list[ImageCandidate]) -> ImagePair:
        """Select two distinct images from the candidate pool."""


class RandomPairSelector:
    """Default pair selector that samples two distinct images uniformly."""

    strategy_name = "random"

    def __init__(self) -> None:
        """Create a selector with cryptographic-quality process-local randomness."""
        self._random = SystemRandom()

    def select_pair(self, images: list[ImageCandidate]) -> ImagePair:
        """Select two distinct images from the candidate pool."""
        if len(images) < 2:
            raise ValueError("At least two images are required to create a comparison pair.")

        left, right = self._random.sample(images, 2)
        return ImagePair(left=left, right=right, strategy=self.strategy_name)


def build_candidates(image_paths: list[Path], image_root: Path) -> list[ImageCandidate]:
    """Create stable candidate ids from paths relative to the configured image root."""
    candidates: list[ImageCandidate] = []
    for path in image_paths:
        relative_path = path.relative_to(image_root)
        candidates.append(
            ImageCandidate(
                image_id=relative_path.as_posix(),
                path=path,
            )
        )
    return candidates


def get_pair_selector(strategy_name: str = "random") -> PairSelector:
    """Return a pair selector by strategy name.

    TODO: Load external selector plugins here once the plugin contract is
    designed. For now, this function makes the extension point explicit.
    """
    if strategy_name != "random":
        raise ValueError(f"Unknown pair selection strategy: {strategy_name}")
    return RandomPairSelector()
