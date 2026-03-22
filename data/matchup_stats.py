"""Matchup profile computation from match history.

Scans match JSON files and computes per-archetype win/loss records
for a given bot.
"""

from __future__ import annotations

from typing import Any

from data.match_history import get_all_matches

__all__ = ["compute_matchup_profile"]


def compute_matchup_profile(
    bot_emoji: str, results_dir: str,
) -> dict[str, dict[str, Any]]:
    """Compute win/loss record per opponent archetype for a bot.

    Args:
        bot_emoji: Emoji identifier of the bot to profile.
        results_dir: Path to directory containing match JSON files.

    Returns:
        Dict of archetype -> {"wins": int, "losses": int, "rate": float}.
        Empty dict if no matches found or bot has no history.
    """
    matches = get_all_matches(results_dir)
    tallies: dict[str, list[int]] = {}  # archetype -> [wins, losses]

    for match in matches:
        stats = match.get("stats", {})
        if bot_emoji not in stats:
            continue

        bot_stats = stats[bot_emoji]
        if "archetype" not in bot_stats:
            continue

        is_winner = match.get("winner") == bot_emoji

        for opp_emoji, opp_stats in stats.items():
            if opp_emoji == bot_emoji:
                continue
            opp_arch = opp_stats.get("archetype")
            if opp_arch is None:
                continue
            if opp_arch not in tallies:
                tallies[opp_arch] = [0, 0]
            if is_winner:
                tallies[opp_arch][0] += 1
            else:
                tallies[opp_arch][1] += 1

    return _build_profile(tallies)


def _build_profile(
    tallies: dict[str, list[int]],
) -> dict[str, dict[str, Any]]:
    """Convert raw tallies to profile dicts with win rate."""
    profile: dict[str, dict[str, Any]] = {}
    for archetype, (wins, losses) in tallies.items():
        total = wins + losses
        rate = round(wins / total * 100, 1) if total > 0 else 0.0
        profile[archetype] = {"wins": wins, "losses": losses, "rate": rate}
    return profile
