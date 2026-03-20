"""XP integration helper — wires XP calculation + profile persistence after a match.

Called by the match runner after match completion. Pure orchestration, no game logic.
"""

from __future__ import annotations

import os
import sqlite3
from typing import Any

from engine.profile_db import (
    DEFAULT_DB_PATH,
    get_or_create_profile,
    init_profile_db,
    update_profile,
)
from engine.xp import calculate_match_xp

__all__ = ["apply_xp_awards", "inject_xp_into_match"]


def apply_xp_awards(
    match_result: dict[str, Any],
    conn: sqlite3.Connection,
) -> dict[str, dict[str, Any]]:
    """Calculate XP, persist to profiles, detect level-ups.

    Returns a dict keyed by emoji with XP breakdown + level info:
        {"A": {"base": 10, "kills": 30, ..., "total": 150, "new_level": 3, "leveled_up": True}}
    """
    xp_map = calculate_match_xp(match_result)
    winner = match_result.get("winner", "none")
    stats = match_result.get("stats", {})
    awards: dict[str, dict[str, Any]] = {}

    for player in match_result["players"]:
        emoji = player["emoji"]
        name = player["name"]
        breakdown = xp_map[emoji]
        bot_stats = stats.get(emoji, {})
        kills = bot_stats.get("kills", 0)

        # Get level before update
        old_profile = get_or_create_profile(conn, name)
        old_level = old_profile["level"]

        # Persist XP
        new_profile = update_profile(
            conn, name,
            xp_earned=breakdown.total,
            kills=kills,
            won=(emoji == winner),
        )
        new_level = new_profile["level"]

        awards[emoji] = {
            "base": breakdown.base,
            "kills": breakdown.kills,
            "survival": breakdown.survival,
            "placement": breakdown.placement,
            "bonuses": breakdown.bonuses,
            "total": breakdown.total,
            "new_level": new_level,
            "leveled_up": new_level > old_level,
        }

    return awards


def inject_xp_into_match(
    match_data: dict[str, Any],
    conn: sqlite3.Connection | None = None,
    *,
    db_path: str | None = None,
    no_xp: bool = False,
) -> None:
    """Calculate XP and inject 'xp_awards' into match_data in-place.

    Either pass an open *conn* or a *db_path* (auto-creates DB + parent dirs).
    When *no_xp* is True, does nothing.
    """
    if no_xp:
        return

    owns_conn = False
    if conn is None:
        path = os.path.realpath(db_path or DEFAULT_DB_PATH)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        conn = init_profile_db(path)
        owns_conn = True

    try:
        match_data["xp_awards"] = apply_xp_awards(match_data, conn)
    finally:
        if owns_conn:
            conn.close()
