"""Output match results to JSON."""

import json
import os
from datetime import datetime, timezone
from typing import Any

__all__ = ["write_match", "build_match_data"]


def write_match(
    match_data: dict[str, Any],
    results_dir: str,
    broadcast_inbox: str | None = None,
) -> str:
    """Write match data to a JSON file. Returns the filepath.

    If ``broadcast_inbox`` is set, also copy the JSON to
    ``{broadcast_inbox}/match_{id:03d}.json`` (directory auto-created).
    """
    os.makedirs(results_dir, exist_ok=True)

    match_id = match_data["match_id"]
    filename = f"match_{match_id:03d}.json"
    filepath = os.path.join(results_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(match_data, f, indent=2)

    if broadcast_inbox:
        os.makedirs(broadcast_inbox, exist_ok=True)
        inbox_path = os.path.join(broadcast_inbox, filename)
        with open(inbox_path, "w", encoding="utf-8") as f:
            json.dump(match_data, f, indent=2)

    return filepath


def build_match_data(
    match_id: int,
    grid_size: int,
    players: list[dict[str, Any]],
    rounds: list[dict[str, Any]],
    eliminations: list[dict[str, Any]],
    winner_emoji: str,
    stats: dict[str, Any],
    duration_rounds: int,
    carryover: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Build the match data structure."""
    return {
        "match_id": match_id,
        "date": datetime.now(timezone.utc).isoformat(),
        "grid_size": grid_size,
        "players": players,
        "rounds": rounds,
        "eliminations": eliminations,
        "winner": winner_emoji,
        "stats": stats,
        "duration_rounds": duration_rounds,
        "carryover": carryover or {},
    }
