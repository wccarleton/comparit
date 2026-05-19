"""Image pair selection strategies.

This module is intentionally small but public within the app architecture. Study
owners should eventually be able to replace the default random strategy with a
balanced design, active-learning sampler, seeded replay, or a custom plugin.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
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


@dataclass(frozen=True)
class SelectionContext:
    """Inputs available to pair-selection algorithms.

    Attributes:
        candidates: All currently eligible images.
        participant_token_id: Current participant token database id, if token
            gating is enabled.
        completed_count: Number of responses already recorded for this token.
        seen_pair_keys: Order-independent image-id pairs already shown to this
            token. A key is `tuple(sorted((left_image_id, right_image_id)))`.
        database_path: Optional SQLite database path. Custom selectors can use
            this to query global response history or other study tables.
    """

    candidates: list[ImageCandidate]
    participant_token_id: int | None
    completed_count: int
    seen_pair_keys: set[tuple[str, str]] = field(default_factory=set)
    database_path: Path | None = None


class PairSelector(Protocol):
    """Interface for selecting the next image pair."""

    strategy_name: str

    def select_pair(self, context: SelectionContext) -> ImagePair:
        """Select two distinct images from the provided selection context."""


class RandomPairSelector:
    """Default pair selector that samples two distinct images uniformly."""

    strategy_name = "random"

    def __init__(self) -> None:
        """Create a selector with cryptographic-quality process-local randomness."""
        self._random = SystemRandom()

    def select_pair(self, context: SelectionContext) -> ImagePair:
        """Select two distinct images from the candidate pool."""
        if len(context.candidates) < 2:
            raise ValueError("At least two images are required to create a comparison pair.")

        left, right = self._random.sample(context.candidates, 2)
        return ImagePair(left=left, right=right, strategy=self.strategy_name)


class ShufflePairSelector:
    """Selector that avoids repeated unordered pairs within a participant token."""

    strategy_name = "shuffle"

    def __init__(self) -> None:
        """Create a selector with process-local randomness."""
        self._random = SystemRandom()

    def select_pair(self, context: SelectionContext) -> ImagePair:
        """Select an unseen unordered pair, resetting after all pairs are seen."""
        if len(context.candidates) < 2:
            raise ValueError("At least two images are required to create a comparison pair.")

        candidates_by_id = {candidate.image_id: candidate for candidate in context.candidates}
        all_pair_keys = {
            tuple(sorted((left.image_id, right.image_id)))
            for left, right in combinations(context.candidates, 2)
        }
        remaining_pair_keys = sorted(all_pair_keys - context.seen_pair_keys)
        if not remaining_pair_keys:
            remaining_pair_keys = sorted(all_pair_keys)

        left_id, right_id = self._random.choice(remaining_pair_keys)
        left = candidates_by_id[left_id]
        right = candidates_by_id[right_id]
        if self._random.choice((True, False)):
            left, right = right, left
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

    TODO: Load external selector plugins here once dynamic plugin discovery is
    designed. For now, this registry makes the extension point explicit.
    """
    selectors: dict[str, PairSelector] = {
        "random": RandomPairSelector(),
        "shuffle": ShufflePairSelector(),
    }
    if strategy_name not in selectors:
        raise ValueError(f"Unknown pair selection strategy: {strategy_name}")
    return selectors[strategy_name]
