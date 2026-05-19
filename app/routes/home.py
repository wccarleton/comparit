"""Homepage routes."""

from urllib.parse import quote

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import PROJECT_ROOT, get_settings
from app.db.tokens import get_token, is_expired, start_token

router = APIRouter()
templates = Jinja2Templates(directory=PROJECT_ROOT / "app" / "templates")


def _token_page_state(token_value: str | None) -> dict[str, str | bool]:
    """Return template state for token-gated access."""
    settings = get_settings()
    if not settings.token_required:
        return {"access_granted": True, "token_message": "", "consent_required": False}

    if not token_value:
        return {
            "access_granted": False,
            "token_message": "This experiment link is missing a participant token.",
        }

    token = get_token(token_value)
    if token is None:
        return {
            "access_granted": False,
            "token_message": "This experiment link is not valid.",
        }

    if token.status == "unused":
        token = start_token(token_value, settings.in_progress_expiry_minutes)

    if token is None or token.status == "revoked":
        return {
            "access_granted": False,
            "token_message": "This experiment link is no longer available.",
        }

    if token.status == "completed":
        return {
            "access_granted": False,
            "token_message": settings.completion_text,
            "token_message_title": "Task complete",
            "token_message_kind": "completed",
        }

    if is_expired(token):
        return {
            "access_granted": False,
            "token_message": settings.token_expired_text,
            "token_message_title": "Link expired",
            "token_message_kind": "expired",
        }

    return {
        "access_granted": True,
        "token_message": "",
        "consent_required": token.consent_accepted_at is None,
    }


def _asset_url(relative_path: str) -> str:
    """Build a browser URL for a configured non-stimulus asset."""
    return f"/assets/{quote(relative_path, safe='/')}"


@router.get("/", response_class=HTMLResponse)
def index(request: Request, t: str | None = None) -> HTMLResponse:
    """Render the Phase 1 landing page."""
    settings = get_settings()
    token_state = _token_page_state(t)
    institution_logo_url = (
        _asset_url(settings.institution_logo) if settings.institution_logo else ""
    )
    institution_logo_alt = settings.institution_logo_alt or f"{settings.institution_name} logo"
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "app_name": settings.app_name,
            "instructions": settings.instructions,
            "project_title": settings.project_title,
            "project_context": settings.project_context,
            "institution_name": settings.institution_name,
            "institution_branding": settings.institution_branding,
            "institution_logo_url": institution_logo_url,
            "institution_logo_alt": institution_logo_alt,
            "consent_text": settings.consent_text,
            "completion_text": settings.completion_text,
            "token_expired_text": settings.token_expired_text,
            "session_mismatch_text": settings.session_mismatch_text,
            "allow_skip": settings.allow_skip,
            "allow_tie": settings.allow_tie,
            "token": t or "",
            "token_required": settings.token_required,
            "comparisons_per_session": settings.comparisons_per_session,
            "consent_required": True,
            **token_state,
        },
    )


@router.get("/health")
def health() -> dict[str, str]:
    """Small health endpoint for local smoke checks and future proxies."""
    return {"status": "ok"}
