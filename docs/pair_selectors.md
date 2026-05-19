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

For now, add a selector class in `app/services/pair_selection.py` and register
it in `get_pair_selector`.

Future plugin discovery can replace the small registry without changing the
selector contract.
