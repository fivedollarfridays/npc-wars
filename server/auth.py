"""API key authentication dependency for FastAPI routes."""

from __future__ import annotations

import logging
import uuid

from fastapi import Header, HTTPException, Request

from server.db import create_api_key, create_player, get_player_by_api_key

_logger = logging.getLogger(__name__)


async def get_current_player(
    request: Request,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> dict:
    """Resolve player from API key or auto-create on first request.

    Returns a player dict.  When a new player is created the dict
    includes ``api_key`` and ``is_new`` keys so the caller can
    surface the key to the client.
    """
    conn = request.app.state.db

    if x_api_key:
        player = get_player_by_api_key(conn, x_api_key)
        if not player:
            client_host = request.client.host if request.client else "unknown"
            _logger.warning(
                "Auth failure: %s from %s", "invalid API key", client_host
            )
            raise HTTPException(status_code=401, detail="Invalid API key")
        return dict(player)

    # Auto-generate player + key on first request
    player_id = uuid.uuid4().hex
    player = create_player(conn, player_id, f"player_{player_id[:8]}")
    key = create_api_key(conn, player_id)
    return {**player, "api_key": key, "is_new": True}


async def require_api_key(
    request: Request,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> dict:
    """Strict auth — requires a valid API key (no auto-create)."""
    client_host = request.client.host if request.client else "unknown"
    if not x_api_key:
        _logger.warning("Auth failure: %s from %s", "missing API key", client_host)
        raise HTTPException(status_code=401, detail="API key required")

    conn = request.app.state.db
    player = get_player_by_api_key(conn, x_api_key)
    if not player:
        _logger.warning("Auth failure: %s from %s", "invalid API key", client_host)
        raise HTTPException(status_code=401, detail="Invalid API key")
    return dict(player)
