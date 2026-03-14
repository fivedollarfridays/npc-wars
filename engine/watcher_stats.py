"""Lifetime stat tracking for The Cringe.

Tracks kills, deaths, match results, win streaks, and per-player
encounter history.  Persists to a JSON file separate from the
pattern-table memory.
"""

from __future__ import annotations

import json
from typing import Any
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_STATS_PATH: str = "data/watcher_stats.json"


@dataclass
class WatcherStats:
    """Cumulative lifetime statistics for The Cringe."""

    matches: int = 0
    wins: int = 0
    kills: int = 0
    human_kills: int = 0
    bot_kills: int = 0
    deaths: int = 0
    current_streak: int = 0
    encounters: dict[str, dict[str, int]] = field(default_factory=dict)

    # -- properties ----------------------------------------------------------

    @property
    def win_rate(self) -> float:
        """Return win percentage (0.0 if no matches played)."""
        return self.wins / self.matches if self.matches > 0 else 0.0

    # -- mutators -------------------------------------------------------------

    def record_kill(self, victim_type: str = "bot") -> None:
        """Increment kill counters for *victim_type* (``human`` or ``bot``)."""
        self.kills += 1
        if victim_type == "human":
            self.human_kills += 1
        else:
            self.bot_kills += 1

    def record_death(self) -> None:
        """Increment the death counter."""
        self.deaths += 1

    def record_match(self, won: bool) -> None:
        """Record a match result, updating wins and streak."""
        self.matches += 1
        if won:
            self.wins += 1
            self.current_streak += 1
        else:
            self.current_streak = 0

    def record_encounter(self, player_id: str, won: bool) -> None:
        """Track an encounter with *player_id*."""
        if player_id not in self.encounters:
            self.encounters[player_id] = {"count": 0, "wins": 0}
        self.encounters[player_id]["count"] += 1
        if won:
            self.encounters[player_id]["wins"] += 1

    # -- serialization --------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary of all stats."""
        return {
            "matches": self.matches,
            "wins": self.wins,
            "kills": self.kills,
            "human_kills": self.human_kills,
            "bot_kills": self.bot_kills,
            "deaths": self.deaths,
            "current_streak": self.current_streak,
            "encounters": dict(self.encounters),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WatcherStats:
        """Reconstruct a ``WatcherStats`` from a serialized dictionary."""
        return cls(
            matches=data.get("matches", 0),
            wins=data.get("wins", 0),
            kills=data.get("kills", 0),
            human_kills=data.get("human_kills", 0),
            bot_kills=data.get("bot_kills", 0),
            deaths=data.get("deaths", 0),
            current_streak=data.get("current_streak", 0),
            encounters=data.get("encounters", {}),
        )


def save_stats(stats: WatcherStats, path: str = DEFAULT_STATS_PATH) -> None:
    """Persist *stats* to a JSON file, creating parent dirs as needed."""
    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(json.dumps(stats.to_dict(), indent=2))


def load_stats(path: str = DEFAULT_STATS_PATH) -> WatcherStats:
    """Load stats from a JSON file; returns empty stats if file is missing."""
    filepath = Path(path)
    if not filepath.exists():
        return WatcherStats()
    data = json.loads(filepath.read_text())
    return WatcherStats.from_dict(data)


__all__ = [
    "DEFAULT_STATS_PATH",
    "WatcherStats",
    "load_stats",
    "save_stats",
]
