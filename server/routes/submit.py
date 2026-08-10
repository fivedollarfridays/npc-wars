"""POST /api/submit-bot route for bot source submission."""

import ast
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.responses import Response
from pydantic import BaseModel, Field

from engine.bot_scanner import scan_bot_source
from server.auth import get_current_player
from server.db import store_bot
from server.middleware.rate_limit import (
    check_rate_limit,
    clear_rate_limit_state,
    record_submission,
)
from server.queue import enqueue_match
from server.submission import build_submission_job

_logger = logging.getLogger(__name__)

router = APIRouter()

# Legacy alias kept for existing test imports
_rate_limits: dict[str, float] = {}


class BotSubmission(BaseModel):
    """Request body for bot submission."""

    source: str = Field(max_length=50_000)


def clear_rate_limits() -> None:
    """Clear all rate limit state (for testing)."""
    _rate_limits.clear()
    clear_rate_limit_state()


def _extract_bot_meta(source: str) -> tuple[str, str]:
    """Extract BOT_NAME and BOT_EMOJI from source via AST.

    Returns (name, emoji) with defaults if not found.
    """
    name, emoji = "Unnamed", "?"
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return name, emoji
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and isinstance(
                    node.value, ast.Constant
                ):
                    if target.id == "BOT_NAME":
                        name = str(node.value.value)
                    elif target.id == "BOT_EMOJI":
                        emoji = str(node.value.value)
    return name, emoji


@router.post("/api/submit-bot", status_code=202, response_model=None)
async def submit_bot(
    body: BotSubmission,
    request: Request,
    player: dict = Depends(get_current_player),
) -> dict[str, Any] | Response:
    """Submit bot source code for validation and queuing."""
    # Rate limit check via middleware dependency
    rate_response = await check_rate_limit(request)
    if rate_response is not None:
        return rate_response

    # Validate source is non-empty
    if not body.source.strip():
        raise HTTPException(status_code=400, detail="Source code is empty")

    # Scan for security violations
    errors = scan_bot_source(body.source)
    if errors:
        _logger.warning(
            "Bot scan violations from player %s: %s",
            player.get("id", "unknown"),
            errors,
        )
        raise HTTPException(status_code=400, detail=errors)

    # Record submission for rate limiting
    record_submission(request)

    # Persist bot
    conn = request.app.state.db
    bot_name, bot_emoji = _extract_bot_meta(body.source)
    bot_id = store_bot(conn, player["id"], bot_name, bot_emoji, body.source)

    job_id = str(uuid.uuid4())

    # UP-3: enqueue a real submission match. The worker runs it through the
    # sandbox (run_sandboxed) against AI fill opponents, then writes a result
    # the SSE replay / share page / ladder pick up unchanged.
    results_dir = getattr(request.app.state, "results_dir", "results")
    enqueue_match(
        build_submission_job(
            job_id=job_id,
            player_id=player["id"],
            bot_id=bot_id,
            source=body.source,
            emoji=bot_emoji,
            results_dir=results_dir,
        )
    )

    # Build response
    content: dict[str, Any] = {"job_id": job_id, "bot_id": bot_id}
    if player.get("is_new"):
        content["api_key"] = player["api_key"]

    headers = getattr(request.state, "rate_limit_headers", {})
    return JSONResponse(
        status_code=202,
        content=content,
        headers=headers,
    )
