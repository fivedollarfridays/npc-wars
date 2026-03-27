"""Rival training API endpoints."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from server.auth import require_api_key
from server.rival_db import ensure_rival_progress, get_rival_progress, is_graduated
from server.rival_debrief import analyze_rival_match
from server.rival_factory import RIVAL_EMOJI
from server.rival_patterns import get_pattern_summary, record_match_patterns

router = APIRouter(prefix="/api/rival", tags=["rival"])


@router.get("/status")
async def rival_status(
    request: Request,
    player: dict = Depends(require_api_key),
) -> dict:
    """Get player's current rival tier and progress."""
    conn = request.app.state.db
    progress = ensure_rival_progress(conn, player["id"])
    return progress


@router.get("/graduated")
async def rival_graduated(
    request: Request,
    player: dict = Depends(require_api_key),
) -> dict:
    """Check whether the player has graduated from rival training."""
    conn = request.app.state.db
    progress = ensure_rival_progress(conn, player["id"])
    graduated = is_graduated(conn, player["id"])
    tiers_beaten = progress["current_tier"] if graduated else progress["current_tier"] - 1
    return {
        "graduated": graduated,
        "graduated_at": progress.get("graduated_at"),
        "tiers_beaten": tiers_beaten,
    }


class RivalChallenge(BaseModel):
    tier: int = Field(ge=1, le=5)


@router.post("/challenge")
async def rival_challenge(
    body: RivalChallenge,
    request: Request,
    player: dict = Depends(require_api_key),
) -> dict:
    """Challenge a specific rival tier (requires graduation)."""
    conn = request.app.state.db
    if not is_graduated(conn, player["id"]):
        raise HTTPException(status_code=403, detail="Must graduate to choose tier")
    return {"status": "queued", "tier": body.tier}


@router.get("/debrief/{match_id}")
async def rival_debrief(
    match_id: int,
    request: Request,
    player: dict = Depends(require_api_key),
) -> dict:
    """Return post-match debrief analysis for a rival training match."""
    results_dir = Path(getattr(request.app.state, "results_dir", "results"))
    match_path = results_dir / f"match_{match_id:03d}.json"
    if not match_path.exists():
        raise HTTPException(status_code=404, detail="Match not found")

    match_data = json.loads(match_path.read_text())

    # Determine player emoji from match data
    player_emoji = _find_player_emoji(match_data, player["id"])

    # Record player action patterns for cross-match learning
    if player_emoji:
        table = record_match_patterns(player["id"], match_data, player_emoji)
        pattern_summary = get_pattern_summary(table, player["id"])
    else:
        pattern_summary = None

    # Get rival tier from progress
    conn = request.app.state.db
    progress = get_rival_progress(conn, player["id"])
    rival_tier = progress["current_tier"] if progress else 1

    return analyze_rival_match(
        match_data, player_emoji, rival_tier, pattern_data=pattern_summary,
    )


def _find_player_emoji(match_data: dict, player_id: str) -> str:
    """Find the player's emoji in match data (non-rival bot)."""
    for p in match_data.get("players", []):
        if p.get("emoji") != RIVAL_EMOJI:
            return p["emoji"]
    # Fallback: first player
    players = match_data.get("players", [])
    return players[0]["emoji"] if players else "\U0001f916"
