"""Match index and query functions.

index_matches scans a results directory and returns lightweight metadata.
Full match data is loaded on demand via get_match.
"""

import json
import os
import re
from typing import Any

__all__ = [
    "index_matches", "get_match", "get_all_matches",
    "list_matches", "get_latest_match", "next_match_id",
]


def _entry_from_match(data: dict[str, Any]) -> dict[str, Any]:
    """Extract index metadata from a full match dict."""
    return {
        "match_id": data["match_id"],
        "date": data["date"],
        "winner": data["winner"],
        "player_count": len(data["players"]),
        "players": [p["emoji"] for p in data["players"]],
        "duration_rounds": data["duration_rounds"],
    }


def index_matches(results_dir: str) -> list[dict[str, Any]]:
    """Scan results_dir and return sorted index of match metadata."""
    if not os.path.isdir(results_dir):
        return []
    entries = []
    for filename in os.listdir(results_dir):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(results_dir, filename)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            entries.append(_entry_from_match(data))
        except (json.JSONDecodeError, OSError):
            continue
    entries.sort(key=lambda e: e["match_id"])
    return entries


def next_match_id(results_dir: str) -> int:
    """Return the next available match_id (max existing + 1, or 1 if empty)."""
    if not os.path.isdir(results_dir):
        return 1
    max_id = 0
    for filename in os.listdir(results_dir):
        m = re.match(r"match_(\d+)\.json$", filename)
        if m:
            max_id = max(max_id, int(m.group(1)))
    return max_id + 1


def get_all_matches(results_dir: str) -> list[dict[str, Any]]:
    """Load and return all match data dicts from results_dir in one pass."""
    if not os.path.isdir(results_dir):
        return []
    matches: list[dict[str, Any]] = []
    for filename in os.listdir(results_dir):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(results_dir, filename)
        try:
            with open(path, encoding="utf-8") as f:
                matches.append(json.load(f))
        except (json.JSONDecodeError, OSError):
            continue
    matches.sort(key=lambda m: m.get("match_id", 0))
    return matches


def get_match(results_dir: str, match_id: int) -> dict[str, Any] | None:
    """Load and return a full match dict by ID, or None if not found."""
    path = os.path.join(results_dir, f"match_{match_id:03d}.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def list_matches(results_dir: str, limit: int | None = None, offset: int = 0,
                 winner: str | None = None, bot: str | None = None,
                 after: str | None = None, before: str | None = None) -> list[dict[str, Any]]:
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


def get_latest_match(results_dir: str) -> dict[str, Any] | None:
    """Return the full match dict with the highest match_id, or None."""
    index = index_matches(results_dir)
    if not index:
        return None
    latest_id = index[-1]["match_id"]
    return get_match(results_dir, latest_id)
