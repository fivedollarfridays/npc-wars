"""Badge API endpoints — public, no auth required."""

from __future__ import annotations

from fastapi import APIRouter, Request

from server.badges import get_player_badges

router = APIRouter(prefix="/api", tags=["badges"])


@router.get("/badges/{player_id}")
async def player_badges(player_id: str, request: Request) -> list:
    """Return all badges with earned status for a player."""
    conn = request.app.state.db
    return get_player_badges(conn, player_id)
