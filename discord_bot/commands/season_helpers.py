"""Season automation helpers and formatters (no discord.py dependency)."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from data.seasons import record_result
from discord_bot.formatters import COLOR_BLUE, COLOR_GOLD, COLOR_GREEN

__all__ = [
    "format_season_created",
    "format_season_standings",
    "format_weekly_summary",
    "check_season_finale",
    "record_match_to_season",
]

_GAME_LABELS = {"kill_switch": "Kill Switch", "code_circuit": "Code Circuit"}


# ---------------------------------------------------------------------------
# Pure formatters
# ---------------------------------------------------------------------------


def format_season_created(name: str, season_id: int, game: str) -> dict[str, Any]:
    """Format confirmation embed for season creation."""
    label = _GAME_LABELS.get(game, game)
    return {
        "title": "\U0001f3c6 Season Created",
        "description": f"**{name}** ({label}) — ID #{season_id}",
        "color": COLOR_GREEN,
        "fields": [],
    }


def format_season_standings(
    season_name: str, standings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Format standings embed with tier labels."""
    if not standings:
        return {
            "title": f"\U0001f4ca {season_name} Standings",
            "description": "No results yet.",
            "color": COLOR_BLUE,
            "fields": [],
        }
    lines = [
        f"{i + 1}. {s['participant']} — {s['points']}pts ({s['tier']})"
        for i, s in enumerate(standings)
    ]
    return {
        "title": f"\U0001f4ca {season_name} Standings",
        "description": "",
        "color": COLOR_BLUE,
        "fields": [
            {"name": "Rankings", "value": "\n".join(lines), "inline": False},
        ],
    }


def format_weekly_summary(
    season_name: str, standings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Format weekly power rankings embed."""
    if not standings:
        return {
            "title": f"\U0001f4e3 {season_name} — Power Rankings",
            "description": "No results yet.",
            "color": COLOR_GOLD,
            "fields": [],
        }
    lines = [
        f"{i + 1}. {s['participant']} — {s['points']}pts ({s['tier']})"
        for i, s in enumerate(standings)
    ]
    return {
        "title": f"\U0001f4e3 {season_name} — Power Rankings",
        "description": "",
        "color": COLOR_GOLD,
        "fields": [
            {"name": "Standings", "value": "\n".join(lines), "inline": False},
        ],
    }


# ---------------------------------------------------------------------------
# Automation helpers
# ---------------------------------------------------------------------------


def _record_ks_results(
    season_id: int, match_data: dict[str, Any], conn: sqlite3.Connection,
) -> None:
    stats = match_data.get("stats", {})
    elims = match_data.get("eliminations", [])
    winner = match_data.get("winner")
    participants = match_data.get("participants", list(stats.keys()))

    elim_order = [e["emoji"] for e in elims]
    placements: dict[str, int] = {}
    if winner:
        placements[winner] = 1
    n = len(participants)
    for idx, emoji in enumerate(elim_order):
        placements[emoji] = n - idx

    for participant in participants:
        kills = stats.get(participant, {}).get("kills", 0)
        placement = placements.get(participant, n)
        record_result(
            season_id,
            {"participant": participant, "kills": kills, "placement": placement},
            conn=conn,
        )


def record_match_to_season(
    season_id: int,
    match_data: dict[str, Any],
    *,
    conn: sqlite3.Connection,
) -> None:
    """Extract per-participant results from match_data and record them."""
    game = match_data.get("game", "kill_switch")
    if game == "code_circuit":
        for entry in match_data.get("results", []):
            record_result(
                season_id,
                {"participant": entry["car"], "position": entry["position"]},
                conn=conn,
            )
    else:
        _record_ks_results(season_id, match_data, conn)


def check_season_finale(
    season_id: int, *, conn: sqlite3.Connection,
) -> bool:
    """Return True if the season has reached its configured total_rounds."""
    row = conn.execute(
        "SELECT config_json FROM seasons WHERE id = ?", (season_id,),
    ).fetchone()
    if row is None:
        return False
    config = json.loads(row["config_json"])
    total = config.get("total_rounds")
    if total is None:
        return False

    count_row = conn.execute(
        "SELECT COUNT(*) as cnt FROM season_results WHERE season_id = ?",
        (season_id,),
    ).fetchone()
    return count_row["cnt"] >= total
