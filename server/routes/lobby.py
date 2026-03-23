"""Lobby HTTP endpoints — join, status, match history."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from server.auth import get_current_player
from server.db import get_bot, get_player_matches
from server.lobby import Lobby

router = APIRouter(prefix="/api/lobby", tags=["lobby"])

_lobby = Lobby()


def get_lobby() -> Lobby:
    """Return the module-level lobby instance (testable via override)."""
    return _lobby


def reset_lobby() -> None:
    """Reset the lobby state (for testing between requests)."""
    _lobby.reset()


@router.post("/join")
async def join_lobby(
    bot_id: int,
    request: Request,
    player: dict = Depends(get_current_player),
) -> dict:
    """Add a player's bot to the lobby."""
    conn = request.app.state.db
    bot = get_bot(conn, bot_id)
    if not bot or bot["player_id"] != player["id"]:
        raise HTTPException(status_code=404, detail="Bot not found")

    lobby = get_lobby()
    bot_config = {
        "name": bot["name"],
        "emoji": bot["emoji"],
        "source": bot["source"],
        "player_id": player["id"],
        "bot_id": bot_id,
    }
    accepted = lobby.join(bot_config)
    if not accepted:
        raise HTTPException(status_code=409, detail="Lobby full or match in progress")

    return {"joined": True, "lobby": lobby.status()}


@router.get("/status")
async def lobby_status() -> dict:
    """Return current lobby state."""
    return get_lobby().status()


@router.get("/history")
async def match_history(
    request: Request,
    player: dict = Depends(get_current_player),
) -> dict:
    """List recent match IDs for this player."""
    conn = request.app.state.db
    matches = get_player_matches(conn, player["id"])
    return {"matches": matches}
