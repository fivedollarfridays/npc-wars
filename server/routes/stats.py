"""Player stats and leaderboard endpoints."""

import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from data.leaderboard import VALID_SORT_FIELDS, aggregate_stats, get_rankings
from data.lifetime_stats import get_lifetime_stats
from data.match_history import get_all_matches, list_matches
from server.rival_db import get_rival_progress

router = APIRouter(prefix="/api", tags=["stats"])


def _emoji_rival_map(
    conn: sqlite3.Connection, emojis: list[str]
) -> dict[str, dict[str, Any]]:
    """Map bot emojis to rival tier info via the bots table."""
    default = {"rival_tier": 0, "graduated": False}
    result: dict[str, dict[str, Any]] = {e: dict(default) for e in emojis}

    # Build emoji -> player_id mapping from bots table
    for emoji in emojis:
        row = conn.execute(
            "SELECT player_id FROM bots WHERE emoji = ? ORDER BY created_at DESC LIMIT 1",
            (emoji,),
        ).fetchone()
        if not row:
            continue
        progress = get_rival_progress(conn, row["player_id"])
        if progress:
            result[emoji] = {
                "rival_tier": progress["current_tier"],
                "graduated": progress.get("graduated_at") is not None,
            }

    return result


@router.get("/stats/{player_id}")
async def player_stats(player_id: str, request: Request) -> dict[str, float]:
    """Return lifetime stat averages for a single player.

    Returns 404 if the player has no match history.
    """
    results_dir: str = request.app.state.results_dir
    stats = get_lifetime_stats(results_dir, player_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Player not found")
    return stats


@router.get("/leaderboard")
async def leaderboard(
    request: Request, sort_by: str = "wins"
) -> list[dict[str, Any]]:
    """Return ranked list of all players sorted by the given stat."""
    if sort_by not in VALID_SORT_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by value. Must be one of: {sorted(VALID_SORT_FIELDS)}",
        )
    results_dir: str = request.app.state.results_dir
    matches = get_all_matches(results_dir)
    if not matches:
        return []
    stats = aggregate_stats(matches)
    rankings = get_rankings(stats, sort_by)

    # Enrich with rival tier badges
    db = getattr(request.app.state, "db", None)
    if db is not None:
        emojis = [r["emoji"] for r in rankings]
        rival_map = _emoji_rival_map(db, emojis)
        for entry in rankings:
            info = rival_map.get(entry["emoji"], {})
            entry["rival_tier"] = info.get("rival_tier", 0)
            entry["graduated"] = info.get("graduated", False)

    return rankings


@router.get("/matches/{player_id}")
async def player_matches(
    player_id: str, request: Request, limit: int = 20
) -> list[dict[str, Any]]:
    """Return recent match index entries for a player (emoji).

    Each entry contains match_id, date, winner, player_count,
    players, and duration_rounds.
    """
    results_dir: str = request.app.state.results_dir
    return list_matches(results_dir, limit=limit, bot=player_id)
