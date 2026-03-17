"""POST /api/submit-bot route for bot source submission."""

import uuid
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from engine.bot_scanner import scan_bot_source
from server.middleware.rate_limit import (
    check_rate_limit,
    clear_rate_limit_state,
    record_submission,
)

router = APIRouter()

# Legacy alias kept for existing test imports
_rate_limits: dict[str, float] = {}


class BotSubmission(BaseModel):
    """Request body for bot submission."""

    source: str


def clear_rate_limits() -> None:
    """Clear all rate limit state (for testing)."""
    _rate_limits.clear()
    clear_rate_limit_state()


@router.post("/api/submit-bot", status_code=202)
async def submit_bot(body: BotSubmission, request: Request) -> dict[str, Any]:
    """Submit bot source code for validation and queuing."""
    # Rate limit check via middleware dependency
    rate_response = await check_rate_limit(request)
    if rate_response is not None:
        return rate_response  # type: ignore[return-value]

    # Validate source is non-empty
    if not body.source.strip():
        return JSONResponse(  # type: ignore[return-value]
            status_code=400,
            content={"errors": ["Source code is empty"]},
        )

    # Scan for security violations
    errors = scan_bot_source(body.source)
    if errors:
        return JSONResponse(  # type: ignore[return-value]
            status_code=400,
            content={"errors": errors},
        )

    # Record submission for rate limiting
    record_submission(request)

    job_id = str(uuid.uuid4())

    # Attach rate limit headers to response
    headers = getattr(request.state, "rate_limit_headers", {})
    return JSONResponse(  # type: ignore[return-value]
        status_code=202,
        content={"job_id": job_id},
        headers=headers,
    )
