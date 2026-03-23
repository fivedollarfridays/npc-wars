"""Bot listing routes — GET /api/bots, GET /api/bots/{bot_id}."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from server.auth import require_api_key
from server.db import get_bot, get_player_bots

router = APIRouter()


@router.get("/api/bots")
async def list_bots(
    request: Request,
    player: dict = Depends(require_api_key),
) -> list[dict]:
    """List all bots for the authenticated player."""
    conn = request.app.state.db
    return get_player_bots(conn, player["id"])


@router.get("/api/bots/{bot_id}")
async def get_bot_detail(
    bot_id: int,
    request: Request,
    player: dict = Depends(require_api_key),
) -> dict:
    """Get a specific bot by ID (must belong to the player)."""
    conn = request.app.state.db
    bot = get_bot(conn, bot_id)
    if bot is None or bot["player_id"] != player["id"]:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot
