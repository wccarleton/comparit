"""Export scaffolding.

Future export code will likely produce CSV or JSONL files for downstream
analysis. Phase 1 only makes the intended boundary explicit.
"""

from pathlib import Path


def describe_export_target(output_dir: Path) -> str:
    """Return a human-readable placeholder export message."""
    # TODO: Export normalized response rows once comparison capture exists.
    return f"Exports will be written to {output_dir}"
