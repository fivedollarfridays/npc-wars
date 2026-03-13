"""Match index and query functions.

index_matches scans a results directory and returns lightweight metadata.
Full match data is loaded on demand via get_match.
"""

import json
import os

__all__ = ["index_matches", "get_match", "list_matches", "get_latest_match"]


def _entry_from_match(data: dict) -> dict:
    """Extract index metadata from a full match dict."""
    return {
        "match_id": data["match_id"],
        "date": data["date"],
        "winner": data["winner"],
        "player_count": len(data["players"]),
        "players": [p["emoji"] for p in data["players"]],
        "duration_rounds": data["duration_rounds"],
    }


def index_matches(results_dir: str) -> list[dict]:
    """Scan results_dir and return sorted index of match metadata."""
    if not os.path.isdir(results_dir):
        return []
    entries = []
    for filename in os.listdir(results_dir):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(results_dir, filename)
        try:
            with open(path) as f:
                data = json.load(f)
            entries.append(_entry_from_match(data))
        except Exception:
            continue
    entries.sort(key=lambda e: e["match_id"])
    return entries


def get_match(results_dir: str, match_id: int) -> dict | None:
    """Load and return a full match dict by ID, or None if not found."""
    path = os.path.join(results_dir, f"match_{match_id:03d}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def list_matches(results_dir: str, limit: int | None = None, offset: int = 0,
                 winner: str | None = None, bot: str | None = None,
                 after: str | None = None, before: str | None = None) -> list[dict]:
    """Return index entries with optional filtering and pagination.

    Filters applied before pagination:
    - winner: emoji must match match winner
    - bot: emoji must appear in players list
    - after/before: ISO date prefix strings (e.g. "2026-06-01")
    """
    entries = index_matches(results_dir)

    if winner is not None:
        entries = [e for e in entries if e["winner"] == winner]
    if bot is not None:
        entries = [e for e in entries if bot in e["players"]]
    if after is not None:
        entries = [e for e in entries if e["date"] > after]
    if before is not None:
        entries = [e for e in entries if e["date"] < before]

    entries = entries[offset:]
    if limit is not None:
        entries = entries[:limit]
    return entries


def get_latest_match(results_dir: str) -> dict | None:
    """Return the full match dict with the highest match_id, or None."""
    index = index_matches(results_dir)
    if not index:
        return None
    latest_id = index[-1]["match_id"]
    return get_match(results_dir, latest_id)
