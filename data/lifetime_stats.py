"""Per-player lifetime stats API.

Computes per-stat averages across all historical matches for a given player.
"""

from typing import Any

from data.leaderboard import aggregate_stats
from data.match_history import get_all_matches

__all__ = ["get_all_lifetime_stats", "get_lifetime_stats"]

# Stats that are raw totals and should be divided by matches_played
_TOTAL_STATS = ("kills", "damage_dealt", "damage_taken")

# Stats that are already rates/averages and should be kept as-is
_RATE_STATS = ("win_rate", "avg_placement")


def _player_averages(player_stats: dict[str, Any]) -> dict[str, float]:
    """Extract per-stat averages from aggregated player stats."""
    played = player_stats["matches_played"]
    if played == 0:
        return {}
    averages: dict[str, float] = {}
    for stat in _TOTAL_STATS:
        if stat in player_stats:
            averages[stat] = player_stats[stat] / played
    for stat in _RATE_STATS:
        averages[stat] = player_stats[stat]
    return averages


def get_all_lifetime_stats(results_dir: str) -> dict[str, dict[str, float]]:
    """Return per-stat averages for ALL players in a single pass.

    Args:
        results_dir: Path to directory containing match JSON files.

    Returns:
        Dict of emoji -> {stat_name: average_value}.
        Missing players are simply absent from the dict.
    """
    matches = get_all_matches(results_dir)
    if not matches:
        return {}
    all_stats = aggregate_stats(matches)
    return {
        emoji: _player_averages(pstats)
        for emoji, pstats in all_stats.items()
        if pstats["matches_played"] > 0
    }


def get_lifetime_stats(results_dir: str, emoji: str) -> dict[str, float]:
    """Return per-stat averages for a player across all historical matches.

    Args:
        results_dir: Path to directory containing match JSON files.
        emoji: Player emoji identifier.

    Returns:
        Dict of stat_name -> average_value, or empty dict if player
        has no history or results_dir doesn't exist.
    """
    all_lifetimes = get_all_lifetime_stats(results_dir)
    return all_lifetimes.get(emoji, {})
