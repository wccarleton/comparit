"""Smoke tests for the Phase 1 application scaffold."""

from fastapi import FastAPI

from app.main import create_app


def test_create_app_returns_fastapi_application() -> None:
    """The app factory should produce a FastAPI instance."""
    app = create_app()

    assert isinstance(app, FastAPI)
    assert app.title == "comparit"
