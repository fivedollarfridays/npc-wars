"""I/O wrapper for rivalry computation.

Loads match data from disk and delegates to pure functions in engine/rivalry.py.
"""

from __future__ import annotations

from typing import Any

from data.match_history import get_all_matches
from engine.rivalry import compute_rivalry_score, compute_rivalry_stats, rivalry_trend

__all__ = ["compute_rivalry"]


def compute_rivalry(
    emoji_a: str, emoji_b: str, results_dir: str,
) -> dict[str, Any]:
    """Load matches and return full rivalry dict with score and trend.

    Returns dict with: emoji_a, emoji_b, wins_a, wins_b, kills_a, kills_b,
    matches, streak, streak_holder, score, trend.
    """
    matches = get_all_matches(results_dir)
    stats = compute_rivalry_stats(emoji_a, emoji_b, matches)
    stats["score"] = compute_rivalry_score(stats)
    stats["trend"] = rivalry_trend(stats)
    # Drop internal-only field
    stats.pop("recent_winners", None)
    return stats
