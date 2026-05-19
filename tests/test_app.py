"""Smoke tests for the Phase 1 application scaffold."""

from fastapi import FastAPI
from starlette.responses import Response

from app.core.cache import add_no_cache_headers, should_prevent_cache
from app.main import create_app


def test_create_app_returns_fastapi_application() -> None:
    """The app factory should produce a FastAPI instance."""
    app = create_app()

    assert isinstance(app, FastAPI)
    assert app.title == "comparit"


def test_no_cache_headers_are_applied() -> None:
    """Participant-facing dynamic responses should not be cached."""
    response = Response()
    add_no_cache_headers(response)
    assert response.headers["Cache-Control"] == "no-store, no-cache, must-revalidate, max-age=0"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["Expires"] == "0"


def test_static_paths_are_excluded_from_no_cache_middleware() -> None:
    """Static assets can keep normal static-file cache behavior."""
    assert should_prevent_cache("/health")
    assert should_prevent_cache("/api/pair")
    assert not should_prevent_cache("/static/css/site.css")
    assert not should_prevent_cache("/assets/logos/institution-logo.svg")
