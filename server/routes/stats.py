"""Player stats and leaderboard endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from data.leaderboard import aggregate_stats, get_rankings
from data.lifetime_stats import get_lifetime_stats
from data.match_history import get_all_matches, list_matches

router = APIRouter(prefix="/api", tags=["stats"])


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
    results_dir: str = request.app.state.results_dir
    matches = get_all_matches(results_dir)
    if not matches:
        return []
    stats = aggregate_stats(matches)
    return get_rankings(stats, sort_by)


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
