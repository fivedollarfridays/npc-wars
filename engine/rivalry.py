"""Pure rivalry computation between bot pairs.

All functions are pure — no I/O. The I/O wrapper lives in data/rivalry_db.py.
"""

from __future__ import annotations

from typing import Any

__all__ = ["compute_rivalry_stats", "compute_rivalry_score", "rivalry_trend"]


def compute_rivalry_stats(
    emoji_a: str, emoji_b: str, matches: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute head-to-head stats between two bots from match data.

    Returns dict with: wins_a, wins_b, kills_a, kills_b, matches,
    streak, streak_holder, recent_winners.
    """
    if emoji_a == emoji_b:
        return _empty_stats()

    wins_a = 0
    wins_b = 0
    kills_a = 0
    kills_b = 0
    total = 0
    streak = 0
    streak_holder: str | None = None
    recent_winners: list[str | None] = []

    for match in matches:
        players = {p["emoji"] for p in match.get("players", [])}
        if emoji_a not in players or emoji_b not in players:
            continue

        total += 1
        match_winner = _match_winner(match, emoji_a, emoji_b)
        if match_winner == emoji_a:
            wins_a += 1
        elif match_winner == emoji_b:
            wins_b += 1
        recent_winners.append(match_winner)

        ka, kb = _count_kills(match, emoji_a, emoji_b)
        kills_a += ka
        kills_b += kb

        streak, streak_holder = _update_streak(
            match_winner, streak, streak_holder,
        )

    return {
        "emoji_a": emoji_a, "emoji_b": emoji_b,
        "wins_a": wins_a, "wins_b": wins_b,
        "kills_a": kills_a, "kills_b": kills_b,
        "matches": total, "streak": streak,
        "streak_holder": streak_holder, "recent_winners": recent_winners,
    }


def _match_winner(
    match: dict[str, Any], emoji_a: str, emoji_b: str,
) -> str | None:
    winner = match.get("winner")
    if winner == emoji_a:
        return emoji_a
    if winner == emoji_b:
        return emoji_b
    return None


def _count_kills(
    match: dict[str, Any], emoji_a: str, emoji_b: str,
) -> tuple[int, int]:
    ka = kb = 0
    for elim in match.get("eliminations", []):
        if elim["emoji"] == emoji_b and elim.get("killed_by") == emoji_a:
            ka += 1
        elif elim["emoji"] == emoji_a and elim.get("killed_by") == emoji_b:
            kb += 1
    return ka, kb


def _update_streak(
    match_winner: str | None, streak: int, streak_holder: str | None,
) -> tuple[int, str | None]:
    if match_winner is None:
        return streak, streak_holder
    if match_winner == streak_holder:
        return streak + 1, streak_holder
    return 1, match_winner


def compute_rivalry_score(stats: dict[str, Any]) -> int:
    """Compute rivalry score 0-100 from stats.

    50 = even, 100 = total A dominance, 0 = total B dominance.
    """
    total = stats["wins_a"] + stats["wins_b"]
    if total == 0:
        return 50
    return int(round(stats["wins_a"] / total * 100))


def rivalry_trend(stats: dict[str, Any]) -> str:
    """Determine trending direction from recent results.

    Returns: "a_rising", "b_rising", "stable", or "none".
    """
    recent = stats.get("recent_winners", [])
    if len(recent) < 2:
        return "none"

    window = [w for w in recent[-3:] if w is not None]
    if not window:
        return "stable"

    a_count = sum(1 for w in window if w == stats["emoji_a"])
    b_count = sum(1 for w in window if w == stats["emoji_b"])

    if a_count > b_count:
        return "a_rising"
    if b_count > a_count:
        return "b_rising"
    return "stable"


def _empty_stats() -> dict[str, Any]:
    return {
        "emoji_a": "", "emoji_b": "",
        "wins_a": 0, "wins_b": 0,
        "kills_a": 0, "kills_b": 0,
        "matches": 0, "streak": 0,
        "streak_holder": None, "recent_winners": [],
    }
