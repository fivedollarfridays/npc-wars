"""POST /api/submit-bot route for bot source submission."""

import time
import uuid
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from engine.bot_scanner import scan_bot_source

router = APIRouter()

# In-memory rate limit tracker: IP -> last submission timestamp
_rate_limits: dict[str, float] = {}

RATE_LIMIT_SECONDS = 30


class BotSubmission(BaseModel):
    """Request body for bot submission."""

    source: str


def clear_rate_limits() -> None:
    """Clear all rate limit state (for testing)."""
    _rate_limits.clear()


@router.post("/api/submit-bot", status_code=202)
async def submit_bot(body: BotSubmission, request: Request) -> dict[str, Any]:
    """Submit bot source code for validation and queuing."""
    client_ip = request.client.host if request.client else "unknown"

    # Rate limit check (with periodic cleanup of stale entries)
    now = time.monotonic()
    if len(_rate_limits) > 1000:
        stale = [ip for ip, ts in _rate_limits.items() if now - ts > RATE_LIMIT_SECONDS]
        for ip in stale:
            del _rate_limits[ip]
    last_time = _rate_limits.get(client_ip)
    if last_time is not None and (now - last_time) < RATE_LIMIT_SECONDS:
        return JSONResponse(  # type: ignore[return-value]
            status_code=429,
            content={"detail": "Rate limited. Try again later."},
        )

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

    # Record submission time for rate limiting
    _rate_limits[client_ip] = now

    job_id = str(uuid.uuid4())
    return {"job_id": job_id}
