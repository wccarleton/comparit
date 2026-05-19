# Pair Selector API

Pair selectors choose the next two images shown to a participant.

The built-in selector registry lives in `app/services/pair_selection.py`.

## Built-In Strategies

- `random`: samples two distinct images uniformly. Repeats are allowed.
- `shuffle`: avoids repeating the same unordered pair for a participant token
  until all possible pairs have been shown, then starts over.

Configure the strategy in `config.toml`:

```toml
[experiment]
pair_selection_strategy = "random"
```

## Selector Contract

A selector implements:

```python
class PairSelector(Protocol):
    strategy_name: str

    def select_pair(self, context: SelectionContext) -> ImagePair:
        ...
```

`SelectionContext` provides:

- `candidates`: list of `ImageCandidate` values available for display.
- `participant_token_id`: current participant token database id, if token
  gating is enabled.
- `completed_count`: number of responses already recorded for this token.
- `seen_pair_keys`: order-independent image-id pairs already shown to this
  token. A key is `tuple(sorted((left_image_id, right_image_id)))`.
- `database_path`: optional SQLite path. Advanced selectors can use this to
  query global response history, image metadata, or other study tables.

A selector returns an `ImagePair`:

```python
ImagePair(
    left=ImageCandidate(...),
    right=ImageCandidate(...),
    strategy="your-strategy-name",
)
```

## Adding a Strategy

For now, custom selectors live in `app/services/pair_selection.py`.

To add one:

1. Add a class with a unique `strategy_name`.
2. Implement `select_pair(self, context: SelectionContext) -> ImagePair`.
3. Raise `ValueError` if fewer than two candidate images are available.
4. Return an `ImagePair` containing two distinct `ImageCandidate` values.
5. Register the selector in `get_pair_selector`.
6. Set `pair_selection_strategy` in `config.toml` to the registered name.

The smallest useful skeleton looks like this:

```python
class YourPairSelector:
    """Short description of what this selector does."""

    strategy_name = "your-strategy-name"

    def select_pair(self, context: SelectionContext) -> ImagePair:
        """Select the next pair for one comparison trial."""
        if len(context.candidates) < 2:
            raise ValueError("At least two images are required to create a comparison pair.")

        # Your selection logic here.
        # You can use:
        # - context.candidates for the currently available image pool
        # - context.participant_token_id for participant-specific behavior
        # - context.completed_count for position within the task
        # - context.seen_pair_keys to avoid or prioritize previous pairs
        # - context.database_path for custom SQLite queries
        left = context.candidates[0]
        right = context.candidates[1]

        return ImagePair(left=left, right=right, strategy=self.strategy_name)
```

Then register it in `get_pair_selector`:

```python
def get_pair_selector(strategy_name: str = "random") -> PairSelector:
    """Return a pair selector by strategy name."""
    selectors: dict[str, PairSelector] = {
        "random": RandomPairSelector(),
        "shuffle": ShufflePairSelector(),
        "your-strategy-name": YourPairSelector(),
    }
    if strategy_name not in selectors:
        raise ValueError(f"Unknown pair selection strategy: {strategy_name}")
    return selectors[strategy_name]
```

Finally, enable it in `config.toml`:

```toml
[experiment]
pair_selection_strategy = "your-strategy-name"
```

## Example: Alphabetical Mirror Selector

This example is intentionally simple and deterministic. It sorts images by
filename, duplicates that sorted list, flips one copy, and pairs each image with
the image at the same position in the flipped list. `completed_count` chooses
the next position, so the sequence advances as responses are recorded.

For six files:

```text
cat-01.svg, cat-02.svg, cat-03.svg, cat-04.svg, cat-05.svg, cat-06.svg
```

the first few pairs would be:

```text
cat-01.svg vs cat-06.svg
cat-02.svg vs cat-05.svg
cat-03.svg vs cat-04.svg
```

Here is the complete selector:

```python
class AlphabeticalMirrorPairSelector:
    """Pair alphabetically sorted images against the reversed sorted list."""

    strategy_name = "alphabetical-mirror"

    def select_pair(self, context: SelectionContext) -> ImagePair:
        """Select a deterministic mirrored pair based on completed count."""
        if len(context.candidates) < 2:
            raise ValueError("At least two images are required to create a comparison pair.")

        sorted_candidates = sorted(
            context.candidates,
            key=lambda candidate: candidate.image_id,
        )
        mirrored_candidates = list(reversed(sorted_candidates))

        index = context.completed_count % len(sorted_candidates)
        left = sorted_candidates[index]
        right = mirrored_candidates[index]

        if left.image_id == right.image_id:
            right = mirrored_candidates[(index + 1) % len(mirrored_candidates)]

        return ImagePair(left=left, right=right, strategy=self.strategy_name)
```

Register it:

```python
def get_pair_selector(strategy_name: str = "random") -> PairSelector:
    """Return a pair selector by strategy name."""
    selectors: dict[str, PairSelector] = {
        "random": RandomPairSelector(),
        "shuffle": ShufflePairSelector(),
        "alphabetical-mirror": AlphabeticalMirrorPairSelector(),
    }
    if strategy_name not in selectors:
        raise ValueError(f"Unknown pair selection strategy: {strategy_name}")
    return selectors[strategy_name]
```

Enable it:

```toml
[experiment]
pair_selection_strategy = "alphabetical-mirror"
```

This is not a recommended scientific sampling design by itself; it is just a
clear example of where custom selection logic belongs.

Future plugin discovery can replace the small registry without changing the
selector contract.
