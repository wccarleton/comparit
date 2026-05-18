"""Experiment-facing routes and lightweight JSON APIs."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.db.responses import ComparisonResponse, count_responses_for_token, record_response
from app.db.tokens import (
    ParticipantToken,
    accept_consent,
    complete_token,
    get_token,
    is_expired,
    start_token,
)
from app.services.image_indexer import discover_images
from app.services.pair_selection import build_candidates, get_pair_selector

logger = logging.getLogger(__name__)
router = APIRouter()


class ChoiceSubmission(BaseModel):
    """Payload sent when a participant selects an image."""

    token: str | None = None
    browser_session_id: str = Field(min_length=1, max_length=128)
    action: Literal["select", "tie", "skip"]
    selected_image_id: str | None = None
    left_image_id: str
    right_image_id: str
    strategy: str
    response_time_ms: int = Field(ge=0)


class ConsentSubmission(BaseModel):
    """Payload sent when a participant accepts consent."""

    token: str | None = None


def _image_url(image_id: str) -> str:
    """Build a browser URL for an image id."""
    return f"/media/images/{image_id}"


def _resolve_image_id(image_id: str) -> Path:
    """Resolve an image id under the configured root without allowing traversal."""
    settings = get_settings()
    image_root = settings.resolved_image_root.resolve()
    requested_path = (image_root / image_id).resolve()

    if image_root != requested_path and image_root not in requested_path.parents:
        raise HTTPException(status_code=404, detail="Image not found")

    if requested_path.suffix.lower() not in settings.allowed_extensions:
        raise HTTPException(status_code=404, detail="Unsupported image type")

    if not requested_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")

    return requested_path


def _require_active_token(
    token_value: str | None,
    require_consent: bool = True,
) -> ParticipantToken | None:
    """Validate or start a token depending on experiment configuration."""
    settings = get_settings()
    if not settings.token_required:
        return None

    if not token_value:
        raise HTTPException(status_code=401, detail="Participant token is required.")

    token = get_token(token_value)
    if token is None:
        raise HTTPException(status_code=403, detail="Participant token is not valid.")

    if token.status == "unused":
        token = start_token(token_value, settings.in_progress_expiry_minutes)

    if token is None or token.status == "revoked":
        raise HTTPException(status_code=403, detail="Participant token is not available.")

    if token.status == "completed":
        raise HTTPException(status_code=409, detail="Participant token is already completed.")

    if is_expired(token):
        raise HTTPException(status_code=403, detail="Participant token has expired.")

    if require_consent and token.consent_accepted_at is None:
        raise HTTPException(status_code=403, detail="Consent has not been accepted.")

    return token


@router.post("/api/consent")
def submit_consent(consent: ConsentSubmission) -> dict[str, object]:
    """Record participant consent acceptance."""
    participant_token = _require_active_token(consent.token, require_consent=False)
    if participant_token is None:
        return {"status": "accepted"}

    accepted_token = accept_consent(participant_token.id)
    return {
        "status": "accepted",
        "consent_accepted": accepted_token is not None
        and accepted_token.consent_accepted_at is not None,
    }


@router.get("/api/pair")
def next_pair(token: str | None = None) -> dict[str, object]:
    """Return the next image pair for the browser UI."""
    settings = get_settings()
    participant_token = _require_active_token(token)
    completed_count = (
        count_responses_for_token(participant_token.id) if participant_token is not None else 0
    )
    if participant_token is not None and completed_count >= settings.comparisons_per_session:
        complete_token(participant_token.id)
        return {
            "completed": True,
            "completed_count": completed_count,
            "comparisons_per_session": settings.comparisons_per_session,
        }

    image_paths = discover_images(settings.resolved_image_root, settings.allowed_extensions)
    candidates = build_candidates(image_paths, settings.resolved_image_root)

    if len(candidates) < 2:
        raise HTTPException(status_code=409, detail="At least two images are required.")

    selector = get_pair_selector()
    pair = selector.select_pair(candidates)

    return {
        "strategy": pair.strategy,
        "completed": False,
        "completed_count": completed_count,
        "comparisons_per_session": settings.comparisons_per_session,
        "allow_skip": settings.allow_skip,
        "allow_tie": settings.allow_tie,
        "left": {
            "id": pair.left.image_id,
            "url": _image_url(pair.left.image_id),
            "label": Path(pair.left.image_id).stem,
        },
        "right": {
            "id": pair.right.image_id,
            "url": _image_url(pair.right.image_id),
            "label": Path(pair.right.image_id).stem,
        },
    }


@router.post("/api/choices")
def submit_choice(choice: ChoiceSubmission) -> dict[str, object]:
    """Persist a browser-submitted comparison response."""
    settings = get_settings()
    participant_token = _require_active_token(choice.token)

    if choice.action == "select" and choice.selected_image_id not in {
        choice.left_image_id,
        choice.right_image_id,
    }:
        raise HTTPException(status_code=400, detail="Selected image must be in the pair.")

    if choice.action == "tie" and not settings.allow_tie:
        raise HTTPException(status_code=400, detail="Tie responses are disabled.")

    if choice.action == "skip" and not settings.allow_skip:
        raise HTTPException(status_code=400, detail="Skip responses are disabled.")

    if choice.action in {"tie", "skip"} and choice.selected_image_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Tie and skip responses cannot select an image.",
        )

    _resolve_image_id(choice.left_image_id)
    _resolve_image_id(choice.right_image_id)
    if choice.selected_image_id is not None:
        _resolve_image_id(choice.selected_image_id)

    response_id = record_response(
        ComparisonResponse(
            participant_token_id=participant_token.id if participant_token is not None else None,
            browser_session_id=choice.browser_session_id,
            left_image_id=choice.left_image_id,
            right_image_id=choice.right_image_id,
            selected_image_id=choice.selected_image_id,
            action=choice.action,
            pair_selection_strategy=choice.strategy,
            response_time_ms=choice.response_time_ms,
        )
    )
    completed_count = (
        count_responses_for_token(participant_token.id) if participant_token is not None else 0
    )
    completed = (
        participant_token is not None and completed_count >= settings.comparisons_per_session
    )
    if completed and participant_token is not None:
        complete_token(participant_token.id)

    logger.info(
        "choice id=%s action=%s selected=%s left=%s right=%s strategy=%s response_time_ms=%s",
        response_id,
        choice.action,
        choice.selected_image_id,
        choice.left_image_id,
        choice.right_image_id,
        choice.strategy,
        choice.response_time_ms,
    )
    return {
        "status": "recorded",
        "response_id": str(response_id),
        "completed": completed,
        "completed_count": completed_count,
        "comparisons_per_session": settings.comparisons_per_session,
    }


@router.get("/media/images/{image_id:path}")
def image_media(image_id: str) -> FileResponse:
    """Serve configured experiment images through a constrained local route."""
    return FileResponse(_resolve_image_id(image_id))
