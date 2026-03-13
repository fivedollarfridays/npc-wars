"""Stats aggregation and rankings from match history.

Pure functions: aggregate_stats takes a list of parsed match dicts.
Use load_match for file I/O at the edges.
"""

import json
from typing import Any

__all__ = ["aggregate_stats", "get_rankings", "get_bot_stats", "load_match"]

VALID_SORT_FIELDS = {"wins", "losses", "kills", "damage_dealt", "damage_taken",
                     "matches_played", "win_rate", "avg_placement"}


def _compute_placements(match: dict[str, Any]) -> dict[str, int]:
    """Return {emoji: placement} for a match (1 = winner, higher = earlier eliminated)."""
    num_players = len(match["players"])
    placements = {}
    # Eliminations are in order: index 0 = first out = worst placement
    for i, elim in enumerate(match["eliminations"]):
        placements[elim["emoji"]] = num_players - i
    placements[match["winner"]] = 1
    return placements


def _empty_bot_stats() -> dict[str, Any]:
    return {
        "wins": 0, "losses": 0, "kills": 0,
        "damage_dealt": 0, "damage_taken": 0,
        "matches_played": 0, "_placement_sum": 0,
        "avg_placement": 0.0, "win_rate": 0.0,
    }


def aggregate_stats(matches: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Aggregate stats across matches. Returns {emoji: stats_dict}."""
    stats = {}

    for match in matches:
        placements = _compute_placements(match)

        for player in match["players"]:
            emoji = player["emoji"]
            if emoji not in stats:
                stats[emoji] = _empty_bot_stats()
            s = stats[emoji]
            m = match["stats"].get(emoji, {})

            s["matches_played"] += 1
            s["kills"] += m.get("kills", 0)
            s["damage_dealt"] += m.get("damage_dealt", 0)
            s["damage_taken"] += m.get("damage_taken", 0)
            s["_placement_sum"] += placements.get(emoji, len(match["players"]))

            if match["winner"] == emoji:
                s["wins"] += 1
            else:
                s["losses"] += 1

    # Compute derived fields
    for emoji, s in stats.items():
        played = s["matches_played"]
        s["win_rate"] = s["wins"] / played if played else 0.0
        s["avg_placement"] = s["_placement_sum"] / played if played else 0.0

    return stats


def get_rankings(stats: dict[str, dict[str, Any]], sort_by: str = "wins") -> list[dict[str, Any]]:
    """Return list of bots sorted by the given stat (descending, except avg_placement ascending).

    Raises ValueError for unknown sort fields.
    """
    if sort_by not in VALID_SORT_FIELDS:
        raise ValueError(f"Unknown sort field: {sort_by!r}. Valid: {sorted(VALID_SORT_FIELDS)}")

    ascending = sort_by == "avg_placement"
    ranked = [{"emoji": emoji, **s} for emoji, s in stats.items()]
    ranked.sort(key=lambda r: r[sort_by], reverse=not ascending)
    return ranked


def get_bot_stats(stats: dict[str, dict[str, Any]], bot_emoji: str) -> dict[str, Any] | None:
    """Return stats for a single bot, or None if not found."""
    return stats.get(bot_emoji)


def load_match(path: str) -> dict[str, Any]:
    """Load a match JSON file. Raises FileNotFoundError if missing."""
    with open(path) as f:
        return json.load(f)
