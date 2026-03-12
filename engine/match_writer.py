"""Output match results to JSON."""

import json
import os
from datetime import datetime, timezone


def write_match(match_data: dict, results_dir: str) -> str:
    """Write match data to a JSON file. Returns the filepath."""
    os.makedirs(results_dir, exist_ok=True)

    match_id = match_data["match_id"]
    filename = f"match_{match_id:03d}.json"
    filepath = os.path.join(results_dir, filename)

    with open(filepath, "w") as f:
        json.dump(match_data, f, indent=2)

    return filepath


def build_match_data(
    match_id: int,
    grid_size: int,
    players: list[dict],
    rounds: list[dict],
    eliminations: list[dict],
    winner_emoji: str,
    stats: dict,
    duration_rounds: int,
) -> dict:
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
    }
