"""Badge definitions and player badge queries for rival training system."""

from __future__ import annotations

import sqlite3
from typing import Any

from server.rival_db import get_rival_progress, is_graduated

TIER_BADGES: dict[int, dict[str, str]] = {
    1: {"name": "Bully Slayer", "emoji": "\u2694\ufe0f", "description": "Defeated The Bully (Tier 1)"},
    2: {"name": "Storm Survivor", "emoji": "\U0001f32a\ufe0f", "description": "Defeated The Storm Chaser (Tier 2)"},
    3: {"name": "Energy Master", "emoji": "\u26a1", "description": "Defeated The Economist (Tier 3)"},
    4: {"name": "Pattern Breaker", "emoji": "\U0001f3af", "description": "Defeated The Counter (Tier 4)"},
    5: {"name": "Mirror Match", "emoji": "\U0001fa9e", "description": "Defeated The Mirror (Tier 5)"},
}

GRADUATION_BADGE: dict[str, str] = {
    "name": "Training Complete",
    "emoji": "\U0001f3c6",
    "description": "Mastered all 5 rival tiers",
}


def get_player_badges(conn: sqlite3.Connection, player_id: str) -> list[dict[str, Any]]:
    """Return all badges with earned status for a player."""
    progress = get_rival_progress(conn, player_id)
    current_tier = progress["current_tier"] if progress else 1
    graduated = is_graduated(conn, player_id) if progress else False

    badges: list[dict[str, Any]] = []
    for tier, badge_info in sorted(TIER_BADGES.items()):
        badges.append({
            "name": badge_info["name"],
            "emoji": badge_info["emoji"],
            "description": badge_info["description"],
            "tier": tier,
            "earned": current_tier > tier or (current_tier == tier and graduated),
        })

    badges.append({
        "name": GRADUATION_BADGE["name"],
        "emoji": GRADUATION_BADGE["emoji"],
        "description": GRADUATION_BADGE["description"],
        "tier": 0,
        "earned": graduated,
    })

    return badges
