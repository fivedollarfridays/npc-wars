"""Cosmetic store API — browse, buy, equip, coin balance."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from server.auth import require_api_key
from server.cosmetic_db import (
    equip_cosmetic,
    get_coin_balance,
    get_player_inventory,
    purchase_cosmetic,
    unequip_cosmetic,
)
from server.cosmetics import COSMETIC_CATALOG

router = APIRouter(prefix="/api", tags=["cosmetics"])


@router.get("/store")
async def browse_store() -> list[dict]:
    """Browse the full cosmetic catalog."""
    return [{"id": k, **v} for k, v in COSMETIC_CATALOG.items()]


@router.get("/coins")
async def coin_balance(
    request: Request,
    player: dict = Depends(require_api_key),
) -> dict:
    """Get player's coin balance."""
    conn = request.app.state.db
    balance = get_coin_balance(conn, player["id"])
    return {"balance": balance}


@router.get("/inventory")
async def player_inventory(
    request: Request,
    player: dict = Depends(require_api_key),
) -> list[dict]:
    """List player's owned cosmetics."""
    conn = request.app.state.db
    return get_player_inventory(conn, player["id"])


@router.post("/store/buy")
async def buy_cosmetic(
    cosmetic_id: str,
    request: Request,
    player: dict = Depends(require_api_key),
) -> dict:
    """Purchase a cosmetic item."""
    conn = request.app.state.db
    success, message = purchase_cosmetic(conn, player["id"], cosmetic_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


@router.post("/inventory/equip")
async def equip(
    cosmetic_id: str,
    request: Request,
    player: dict = Depends(require_api_key),
) -> dict:
    """Equip a cosmetic item."""
    conn = request.app.state.db
    ok = equip_cosmetic(conn, player["id"], cosmetic_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Cannot equip (not owned or invalid)")
    return {"equipped": True, "cosmetic_id": cosmetic_id}


@router.post("/inventory/unequip")
async def unequip(
    cosmetic_id: str,
    request: Request,
    player: dict = Depends(require_api_key),
) -> dict:
    """Unequip a cosmetic item."""
    conn = request.app.state.db
    ok = unequip_cosmetic(conn, player["id"], cosmetic_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Not equipped")
    return {"unequipped": True, "cosmetic_id": cosmetic_id}
