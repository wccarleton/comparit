"""FastAPI entrypoint for comparit.

This module intentionally keeps startup simple in Phase 1. Later phases can add
application lifespan hooks for migrations, background jobs, and deployment
health checks without changing how users launch the app.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.cache import NoCacheMiddleware
from app.core.config import get_settings
from app.routes import experiment, home

BASE_DIR = Path(__file__).resolve().parent


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        description="Pairwise image comparison experiment scaffold.",
    )
    app.add_middleware(NoCacheMiddleware)

    app.mount(
        "/static",
        StaticFiles(directory=BASE_DIR / "static"),
        name="static",
    )
    app.include_router(experiment.router)
    app.include_router(home.router)

    return app


app = create_app()
