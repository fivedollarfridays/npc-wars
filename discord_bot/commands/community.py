"""Community engagement commands -- Bot of Week, Bounty Challenges, Watcher Stats."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

__all__ = ["select_bot_of_week", "create_bounty_challenge", "format_watcher_stats"]

_BUDGET_THRESHOLD = 75


def _score_bot(profile: dict) -> float:
    """Calculate engagement score: creativity (unique_actions) + effectiveness (win_rate)."""
    return profile.get("unique_actions", 0) * 2 + profile.get("win_rate", 0.0) * 10


def select_bot_of_week(profiles: list[dict]) -> dict | None:
    """Select the highest-scoring bot under the budget threshold."""
    eligible = [p for p in profiles if p.get("line_budget", 999) <= _BUDGET_THRESHOLD]
    if not eligible:
        return None

    best = max(eligible, key=_score_bot)
    return {
        "name": best["name"],
        "emoji": best["emoji"],
        "author": best.get("author", "unknown"),
        "score": _score_bot(best),
        "reason": (
            f"Creative play ({best.get('unique_actions', 0)} unique actions) "
            f"with {best.get('win_rate', 0):.0%} win rate"
        ),
    }


def create_bounty_challenge(
    target_bot: str, description: str, challenges_path: str
) -> dict:
    """Create a bounty challenge and persist it to JSON."""
    challenges: list[dict] = []
    if os.path.exists(challenges_path):
        with open(challenges_path) as f:
            challenges = json.load(f)

    challenge = {
        "target": target_bot,
        "description": description,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    challenges.append(challenge)

    with open(challenges_path, "w") as f:
        json.dump(challenges, f, indent=2)

    return challenge


def format_watcher_stats(stats_path: str) -> dict:
    """Load watcher stats from JSON and compute derived fields."""
    defaults = {
        "matches": 0,
        "kills": 0,
        "deaths": 0,
        "current_streak": 0,
        "win_rate": 0.0,
    }
    try:
        with open(stats_path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return defaults

    matches = data.get("matches", 0)
    deaths = data.get("deaths", 0)
    win_rate = (matches - deaths) / matches if matches > 0 else 0.0

    return {
        "matches": matches,
        "kills": data.get("kills", 0),
        "deaths": deaths,
        "current_streak": data.get("current_streak", 0),
        "win_rate": round(win_rate, 3),
    }
