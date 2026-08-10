"""API key authentication dependency for FastAPI routes."""

from __future__ import annotations

import hmac
import logging
import os
import re
import uuid

from fastapi import Header, HTTPException, Request

from server.db import create_api_key, create_player, get_player_by_api_key
from server.player_refs import resolve_player_by_ref

_logger = logging.getLogger(__name__)

#: Dev-only opt-in that re-enables keyless auto-create.  Exact match on "1"
#: only — unset, blank, "true", "yes" etc. all keep the endpoint locked.
KEYLESS_OPT_IN_ENV = "NPCWARS_ALLOW_KEYLESS"

#: Single provisioned key for a trusted relay acting on behalf of players.
SERVICE_KEY_ENV = "NPCWARS_SERVICE_API_KEY"

#: Opaque delegated-identity token.  Never logged, stored or rendered raw.
PLAYER_REF_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,128}$")


def keyless_allowed() -> bool:
    """True only when the keyless dev opt-in is set to exactly ``"1"``."""
    return os.environ.get(KEYLESS_OPT_IN_ENV) == "1"


def service_api_key() -> str | None:
    """Return the provisioned service key, or None when not configured."""
    return os.environ.get(SERVICE_KEY_ENV) or None


def is_service_key(candidate: str | None) -> bool:
    """Constant-time check that *candidate* is the provisioned service key."""
    configured = service_api_key()
    if not configured or not candidate:
        return False
    return hmac.compare_digest(candidate, configured)


def _client_host(request: Request) -> str:
    """Best-effort client host for auth logging."""
    return request.client.host if request.client else "unknown"


def _reject_unauthorized_ref(
    request: Request,
    player_ref: str | None,
    detail: str = "X-Player-Ref requires the service API key",
) -> None:
    """403 when ``X-Player-Ref`` arrives where delegation is not allowed.

    Delegation is never silently ignored — a spoof attempt is always loud.
    """
    if player_ref is None:
        return
    _logger.warning(
        "Auth failure: %s from %s", "unauthorized player ref", _client_host(request)
    )
    raise HTTPException(status_code=403, detail=detail)


def _resolve_delegated(request: Request, player_ref: str | None) -> dict:
    """Resolve the player a service-key request is acting on behalf of.

    The service key must always name a player: a missing or malformed
    ``X-Player-Ref`` is a 400.  The ref value itself is never logged.
    """
    if not player_ref or not PLAYER_REF_PATTERN.match(player_ref):
        _logger.warning(
            "Auth failure: %s from %s",
            "service key without a valid player ref",
            _client_host(request),
        )
        raise HTTPException(
            status_code=400, detail="X-Player-Ref required for service key"
        )
    return dict(resolve_player_by_ref(request.app.state.db, player_ref))


async def get_current_player(
    request: Request,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    x_player_ref: str | None = Header(None, alias="X-Player-Ref"),
) -> dict:
    """Resolve the acting player from API key headers.

    Three shapes are accepted:

    * service key + ``X-Player-Ref`` — delegated identity for the relay
    * a known player API key — that player
    * no key at all — auto-create, but only behind the keyless dev opt-in

    Any other ``X-Player-Ref`` use is a loud 403: delegation is never
    silently ignored.
    """
    if is_service_key(x_api_key):
        return _resolve_delegated(request, x_player_ref)

    _reject_unauthorized_ref(request, x_player_ref)

    conn = request.app.state.db

    if x_api_key:
        player = get_player_by_api_key(conn, x_api_key)
        if not player:
            _logger.warning(
                "Auth failure: %s from %s", "invalid API key", _client_host(request)
            )
            raise HTTPException(status_code=401, detail="Invalid API key")
        return dict(player)

    if not keyless_allowed():
        _logger.warning(
            "Auth failure: %s from %s", "missing API key", _client_host(request)
        )
        raise HTTPException(status_code=401, detail="API key required")

    # Auto-generate player + key on first request (dev opt-in only)
    player_id = uuid.uuid4().hex
    player = create_player(conn, player_id, f"player_{player_id[:8]}")
    key = create_api_key(conn, player_id)
    return {**player, "api_key": key, "is_new": True}


async def require_api_key(
    request: Request,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    x_player_ref: str | None = Header(None, alias="X-Player-Ref"),
) -> dict:
    """Strict auth — requires a valid API key (no auto-create, no delegation)."""
    _reject_unauthorized_ref(
        request,
        x_player_ref,
        detail="Delegated identity is not supported on this endpoint",
    )

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
