"""HTTP cache helpers."""

from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class NoCacheMiddleware(BaseHTTPMiddleware):
    """Prevent caching of participant-facing dynamic responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add no-cache headers to non-static responses."""
        response = await call_next(request)
        if should_prevent_cache(request.url.path):
            add_no_cache_headers(response)
        return response


def should_prevent_cache(path: str) -> bool:
    """Return whether a response path should receive no-cache headers."""
    return not path.startswith(("/static/", "/assets/"))


def add_no_cache_headers(response: Response) -> None:
    """Apply conservative no-cache headers to a response."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
