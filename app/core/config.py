"""Configuration loading for comparit.

The app uses a small TOML file so researchers can configure local paths without
learning a larger settings system. Pydantic validates and normalizes the values
we read from disk.
"""

import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.toml"


class Settings(BaseSettings):
    """Runtime settings used across the application."""

    app_name: str = "comparit"
    debug: bool = True
    base_url: str = "http://127.0.0.1:8000"
    instructions: str = (
        "Compare the two images and select the one that best matches the study prompt."
    )
    project_title: str = "Demo Image Comparison Study"
    project_context: str = (
        "You will compare pairs of images and choose the one that best matches the prompt."
    )
    institution_name: str = "Your Institution"
    institution_branding: str = "Research demo"
    consent_text: str = (
        "I understand that my responses and response times will be recorded for this "
        "study. I understand that I can stop participating by closing the browser tab."
    )
    completion_text: str = (
        "Thank you. Your comparison task is complete and your responses have been recorded."
    )
    token_expired_text: str = (
        "This experiment link has expired. Please contact the study organizer if you "
        "believe this is an error."
    )
    allow_skip: bool = True
    allow_tie: bool = False
    token_required: bool = True
    comparisons_per_session: int = 20
    token_validity_days: int = 28
    in_progress_expiry_minutes: int = 1440
    database_path: Path = Field(default=Path("data/comparit.sqlite3"))
    image_root: Path = Field(default=Path("data/demo_images/cats"))
    allowed_extensions: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".webp", ".svg")
    export_output_dir: Path = Field(default=Path("exports"))

    model_config = SettingsConfigDict(env_prefix="COMPARIT_")

    def resolve_path(self, path: Path) -> Path:
        """Resolve relative config paths from the project root."""
        if path.is_absolute():
            return path
        return PROJECT_ROOT / path

    @property
    def resolved_database_path(self) -> Path:
        """Absolute SQLite database path."""
        return self.resolve_path(self.database_path)

    @property
    def resolved_image_root(self) -> Path:
        """Absolute image root path."""
        return self.resolve_path(self.image_root)

    @property
    def resolved_export_output_dir(self) -> Path:
        """Absolute export output directory."""
        return self.resolve_path(self.export_output_dir)


def _read_toml_config(path: Path) -> dict[str, Any]:
    """Read nested TOML settings from disk if a config file exists."""
    if not path.exists():
        return {}

    with path.open("rb") as config_file:
        raw = tomllib.load(config_file)

    return {
        "app_name": raw.get("app", {}).get("name", "comparit"),
        "debug": raw.get("app", {}).get("debug", True),
        "base_url": raw.get("app", {}).get("base_url", "http://127.0.0.1:8000"),
        "instructions": raw.get("experiment", {}).get(
            "instructions",
            "Compare the two images and select the one that best matches the study prompt.",
        ),
        "project_title": raw.get("experiment", {}).get(
            "project_title",
            "Demo Image Comparison Study",
        ),
        "project_context": raw.get("experiment", {}).get(
            "project_context",
            "You will compare pairs of images and choose the one that best matches the prompt.",
        ),
        "institution_name": raw.get("experiment", {}).get(
            "institution_name",
            "Your Institution",
        ),
        "institution_branding": raw.get("experiment", {}).get(
            "institution_branding",
            "Research demo",
        ),
        "consent_text": raw.get("experiment", {}).get(
            "consent_text",
            "I understand that my responses and response times will be recorded for this "
            "study. I understand that I can stop participating by closing the browser tab.",
        ),
        "completion_text": raw.get("experiment", {}).get(
            "completion_text",
            "Thank you. Your comparison task is complete and your responses have been recorded.",
        ),
        "token_expired_text": raw.get("experiment", {}).get(
            "token_expired_text",
            "This experiment link has expired. Please contact the study organizer if you "
            "believe this is an error.",
        ),
        "allow_skip": raw.get("experiment", {}).get("allow_skip", True),
        "allow_tie": raw.get("experiment", {}).get("allow_tie", False),
        "token_required": raw.get("experiment", {}).get("token_required", True),
        "comparisons_per_session": raw.get("experiment", {}).get(
            "comparisons_per_session",
            20,
        ),
        "token_validity_days": raw.get("experiment", {}).get("token_validity_days", 28),
        "in_progress_expiry_minutes": raw.get("experiment", {}).get(
            "in_progress_expiry_minutes",
            1440,
        ),
        "database_path": Path(raw.get("database", {}).get("path", "data/comparit.sqlite3")),
        "image_root": Path(raw.get("images", {}).get("image_root", "data/demo_images/cats")),
        "allowed_extensions": tuple(
            raw.get("images", {}).get(
                "allowed_extensions",
                [".jpg", ".jpeg", ".png", ".webp", ".svg"],
            )
        ),
        "export_output_dir": Path(raw.get("exports", {}).get("output_dir", "exports")),
    }


@lru_cache
def get_settings(config_path: Path = DEFAULT_CONFIG_PATH) -> Settings:
    """Return cached application settings.

    Environment variables with the `COMPARIT_` prefix are supported by
    `BaseSettings`. Values read from TOML are passed explicitly, so TOML remains
    the clearest configuration source for local Phase 1 usage.
    """
    return Settings(**_read_toml_config(config_path))
