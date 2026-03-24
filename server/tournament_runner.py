"""Automated tournament match runner."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from engine.game import run_match
from server.tournament import Tournament
from server.tournament_db import get_tournament, update_tournament


def _build_bot_config(conn: sqlite3.Connection, player_id: str) -> dict[str, Any]:
    """Build a bot config dict from the player's most recent bot."""
    rows = conn.execute(
        "SELECT * FROM bots WHERE player_id = ? ORDER BY id DESC LIMIT 1",
        (player_id,),
    ).fetchall()
    if not rows:
        raise ValueError(f"No bot found for player {player_id}")
    bot = dict(rows[0])
    return {
        "name": bot["name"],
        "emoji": bot["emoji"],
        "source": bot["source"],
        "player_id": player_id,
        "bot_id": bot["id"],
    }


def _next_match_id(conn: sqlite3.Connection) -> int:
    """Get the next available match ID."""
    row = conn.execute(
        "SELECT COALESCE(MAX(match_id), 0) + 1 AS next_id FROM match_players"
    ).fetchone()
    return row["next_id"] if row else 1


def run_tournament_round(
    conn: sqlite3.Connection, tournament_id: int
) -> list[dict[str, Any]]:
    """Execute all pending matches in the current tournament round.

    Returns list of match results.
    """
    row = get_tournament(conn, tournament_id)
    if row is None:
        return []

    bracket_data = json.loads(row["bracket_json"])
    if not bracket_data or not bracket_data.get("rounds"):
        return []

    tournament = Tournament.from_dict(bracket_data)
    pending = tournament.get_pending_matches()
    if not pending:
        return []

    current_round = tournament.rounds[-1]
    results: list[dict[str, Any]] = []

    for match in current_round:
        if match["results"] is not None:
            continue

        match_idx = current_round.index(match)
        bot_configs = [_build_bot_config(conn, pid) for pid in match["group"]]
        mid = _next_match_id(conn)

        match_result = run_match(
            bot_configs, match_id=mid, map_name=row["map_name"] or "arena"
        )

        # Map bot names back to player IDs for bracket advancement
        name_to_pid = {c["name"]: c["player_id"] for c in bot_configs}
        raw_players = match_result.get("players", [])
        placements = [
            p.get("player_id") or name_to_pid.get(p["name"], p["name"])
            for p in raw_players
        ]
        winner_name = match_result.get("winner", "")

        tournament.record_result(
            match_idx,
            {"winner": winner_name, "placements": placements},
            match_result["match_id"],
        )
        results.append(match_result)

    update_tournament(
        conn,
        tournament_id,
        json.dumps(tournament.to_dict()),
        tournament.status,
        tournament.winner,
    )

    return results
