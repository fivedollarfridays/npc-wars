"""Tournament HTTP endpoints — create, join, run, results."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request

from server.auth import require_api_key
from server.middleware.rate_limit import check_tournament_rate_limit
from server.db import get_bot
from server.tournament import Tournament, VALID_SIZES
from server.tournament_db import (
    create_tournament as db_create,
    get_tournament as db_get,
    list_tournaments as db_list,
    update_tournament as db_update,
)
from server.tournament_runner import run_tournament_round

router = APIRouter(prefix="/api/tournament", tags=["tournament"])


@router.post("/create")
async def create_tournament(
    request: Request,
    name: str,
    size: int = 8,
    map_name: str = "arena",
    _player: dict = Depends(require_api_key),
) -> dict:
    """Create a new tournament."""
    check_tournament_rate_limit(request)
    if size not in VALID_SIZES:
        raise HTTPException(status_code=400, detail=f"Size must be one of {VALID_SIZES}")
    conn = request.app.state.db
    t = Tournament(name, size)
    tid = db_create(conn, name, size, map_name)
    db_update(conn, tid, json.dumps(t.to_dict()), t.status, t.winner)
    return {"tournament_id": tid, "name": name, "size": size, "status": "open"}


@router.post("/{tournament_id}/join")
async def join_tournament(
    tournament_id: int,
    bot_id: int,
    request: Request,
    player: dict = Depends(require_api_key),
) -> dict:
    """Join a tournament with a bot."""
    conn = request.app.state.db
    row = db_get(conn, tournament_id)
    if not row:
        raise HTTPException(status_code=404, detail="Tournament not found")
    bot = get_bot(conn, bot_id)
    if not bot or bot["player_id"] != player["id"]:
        raise HTTPException(status_code=404, detail="Bot not found")

    t = Tournament.from_dict(json.loads(row["bracket_json"]))
    if not t.add_player(player["id"]):
        raise HTTPException(status_code=409, detail="Cannot join tournament")

    if t.is_full():
        t.seed_bracket()

    db_update(conn, tournament_id, json.dumps(t.to_dict()), t.status, t.winner)
    return {"joined": True, "players": len(t.players), "status": t.status}


@router.get("/{tournament_id}")
async def get_tournament(tournament_id: int, request: Request) -> dict:
    """Get tournament status and bracket."""
    conn = request.app.state.db
    row = db_get(conn, tournament_id)
    if not row:
        raise HTTPException(status_code=404, detail="Tournament not found")
    bracket = json.loads(row["bracket_json"])
    return {
        "tournament_id": row["id"],
        "name": row["name"],
        "size": row["size"],
        "status": bracket.get("status", row["status"]),
        "players": bracket.get("players", []),
        "rounds": bracket.get("rounds", []),
        "winner": bracket.get("winner"),
    }


@router.post("/{tournament_id}/run-round")
async def run_round(
    tournament_id: int,
    request: Request,
    _player: dict = Depends(require_api_key),
) -> dict:
    """Execute all pending matches in the current round."""
    conn = request.app.state.db
    row = db_get(conn, tournament_id)
    if not row:
        raise HTTPException(status_code=404, detail="Tournament not found")
    results = run_tournament_round(conn, tournament_id)
    return {"results": results, "matches_played": len(results)}


@router.get("/{tournament_id}/results")
async def get_results(tournament_id: int, request: Request) -> dict:
    """Get final results."""
    conn = request.app.state.db
    row = db_get(conn, tournament_id)
    if not row:
        raise HTTPException(status_code=404, detail="Tournament not found")
    bracket = json.loads(row["bracket_json"])
    return {
        "tournament_id": row["id"],
        "name": row["name"],
        "status": bracket.get("status", row["status"]),
        "winner": bracket.get("winner"),
        "rounds": bracket.get("rounds", []),
    }


@router.get("s")
async def list_tournaments_endpoint(request: Request) -> dict:
    """List active/recent tournaments."""
    conn = request.app.state.db
    rows = db_list(conn)
    tournaments = []
    for r in rows:
        bracket = json.loads(r["bracket_json"])
        tournaments.append({
            "tournament_id": r["id"],
            "name": r["name"],
            "size": r["size"],
            "status": bracket.get("status", r["status"]),
            "winner": bracket.get("winner"),
        })
    return {"tournaments": tournaments}
