"""Per-player pattern persistence for rival training system.

Wraps PatternTable from engine/watcher_memory.py. Stores one JSON file
per player under data/rival_patterns/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.watcher_memory import PatternTable

DEFAULT_PATTERNS_DIR = "data/rival_patterns"

_HIT_TYPES = frozenset({"hit", "ranged_hit"})
_LOW_HP_THRESHOLD = 30
_STORM_MARGIN = 2


def load_player_patterns(
    player_id: str, *, base_dir: str = DEFAULT_PATTERNS_DIR,
) -> PatternTable:
    """Load a player's pattern table from disk, or return empty."""
    path = Path(base_dir) / f"{player_id}.json"
    if not path.exists():
        return PatternTable()
    data = json.loads(path.read_text())
    return PatternTable.from_dict(data)


def save_player_patterns(
    player_id: str, table: PatternTable, *, base_dir: str = DEFAULT_PATTERNS_DIR,
) -> None:
    """Save a player's pattern table to disk."""
    path = Path(base_dir) / f"{player_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(table.to_dict(), indent=2))


def record_match_patterns(
    player_id: str,
    match_data: dict[str, Any],
    player_emoji: str,
    *,
    base_dir: str = DEFAULT_PATTERNS_DIR,
) -> PatternTable:
    """Extract player actions per round, classify contexts, record patterns."""
    table = load_player_patterns(player_id, base_dir=base_dir)
    grid_size = match_data.get("grid_size", 10)

    for rnd in match_data.get("rounds", []):
        positions = rnd.get("positions", [])
        events = rnd.get("events", [])
        storm_border = rnd.get("storm_border", 0)

        player_pos = _find_player(positions, player_emoji)
        if player_pos is None or not player_pos.get("alive", True):
            continue

        enemies = _alive_enemies(positions, player_emoji)
        action = player_pos.get("action", "rest").split()[0]
        contexts = _classify_context(
            player_pos, enemies, storm_border, grid_size, events, player_emoji,
        )

        for ctx in contexts:
            table.record(player_id, ctx, action)

    save_player_patterns(player_id, table, base_dir=base_dir)
    return table


def get_pattern_summary(
    table: PatternTable, player_id: str,
) -> dict[str, dict[str, float]]:
    """Return {context: {action: probability}} for a player."""
    data = table.to_dict()
    player_data = data.get(player_id, {})
    summary: dict[str, dict[str, float]] = {}
    for ctx, actions in player_data.items():
        total = sum(actions.values())
        if total > 0:
            summary[ctx] = {a: c / total for a, c in actions.items()}
    return summary


def compact_for_embed(
    summary: dict[str, dict[str, float]], max_contexts: int = 5,
) -> dict[str, dict[str, float]]:
    """Trim summary to top contexts and top 3 actions each."""
    if not summary:
        return {}
    # Sort contexts by total observation weight (sum of probs ~1 each, use max prob as tiebreaker)
    sorted_ctxs = sorted(
        summary.keys(),
        key=lambda c: max(summary[c].values(), default=0),
        reverse=True,
    )[:max_contexts]

    result: dict[str, dict[str, float]] = {}
    for ctx in sorted_ctxs:
        actions = summary[ctx]
        top_actions = sorted(actions.items(), key=lambda x: x[1], reverse=True)[:3]
        result[ctx] = {a: round(p, 3) for a, p in top_actions}
    return result


# --- internal helpers ---


def _find_player(
    positions: list[dict[str, Any]], emoji: str,
) -> dict[str, Any] | None:
    """Find player position dict by emoji."""
    for pos in positions:
        if pos["emoji"] == emoji:
            return pos
    return None


def _alive_enemies(
    positions: list[dict[str, Any]], player_emoji: str,
) -> list[dict[str, Any]]:
    """Return alive enemy positions."""
    return [
        p for p in positions
        if p["emoji"] != player_emoji and p.get("alive", True)
    ]


def _classify_context(
    player: dict[str, Any],
    enemies: list[dict[str, Any]],
    storm_border: int,
    grid_size: int,
    events: list[dict[str, Any]],
    player_emoji: str,
) -> list[str]:
    """Classify which contexts apply to the player this round."""
    contexts: list[str] = []

    # after_damage: was hit this round
    if any(
        e.get("type") in _HIT_TYPES and e.get("target") == player_emoji
        for e in events
    ):
        contexts.append("after_damage")

    # at_range_1: adjacent to nearest enemy (Manhattan distance 1)
    if enemies:
        min_dist = min(
            abs(e["x"] - player["x"]) + abs(e["y"] - player["y"])
            for e in enemies
        )
        if min_dist == 1:
            contexts.append("at_range_1")

    # below_30_hp
    if player.get("hp", 100) < _LOW_HP_THRESHOLD:
        contexts.append("below_30_hp")

    # storm_closing: near storm border
    if storm_border > 0:
        low = storm_border + _STORM_MARGIN
        high = grid_size - storm_border - _STORM_MARGIN
        px, py = player["x"], player["y"]
        if px < low or px >= high or py < low or py >= high:
            contexts.append("storm_closing")

    return contexts


__all__ = [
    "compact_for_embed",
    "get_pattern_summary",
    "load_player_patterns",
    "record_match_patterns",
    "save_player_patterns",
]
