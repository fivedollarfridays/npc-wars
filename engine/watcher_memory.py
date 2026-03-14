"""Pattern table for tracking human behavioral frequencies.

Stores per-player frequency maps keyed by context, recording how often
each action is taken. Used by The Cringe to learn and counter patterns.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

CONTEXTS: list[str] = [
    "after_damage",
    "at_range_1",
    "below_30_hp",
    "storm_closing",
    "override_detected",
]

GLOBAL_PROFILE: str = "__global__"

SESSION_RETENTION: float = 0.7
CROSS_SESSION_RETENTION: float = 0.3


class PatternTable:
    """Frequency counter for per-player behavioral patterns.

    Storage layout: player_id -> context -> action -> count
    """

    def __init__(self) -> None:
        self._data: dict[str, dict[str, dict[str, float | int]]] = {}

    def record(self, player_id: str, context: str, action: str) -> None:
        """Increment action count for both the player and the global profile."""
        for pid in (player_id, GLOBAL_PROFILE):
            player = self._data.setdefault(pid, {})
            ctx = player.setdefault(context, {})
            ctx[action] = ctx.get(action, 0) + 1

    def predict(self, player_id: str, context: str) -> dict[str, float]:
        """Return normalized probability distribution for a player+context.

        Returns empty dict if no data exists.
        """
        counts = self.get_raw_counts(player_id, context)
        if not counts:
            return {}
        total = sum(counts.values())
        return {action: count / total for action, count in counts.items()}

    def get_raw_counts(
        self, player_id: str, context: str
    ) -> dict[str, float | int]:
        """Return raw frequency counts for a player+context."""
        player = self._data.get(player_id, {})
        return dict(player.get(context, {}))

    def players(self) -> set[str]:
        """Return tracked player IDs, excluding the global profile."""
        return {pid for pid in self._data if pid != GLOBAL_PROFILE}

    def to_dict(self) -> dict[str, dict[str, dict[str, float | int]]]:
        """Return a deep copy of the internal data dictionary."""
        return copy.deepcopy(self._data)

    @classmethod
    def from_dict(
        cls, data: dict[str, dict[str, dict[str, float | int]]]
    ) -> PatternTable:
        """Reconstruct a PatternTable from a serialized data dictionary."""
        pt = cls()
        pt._data = copy.deepcopy(data)
        return pt


def decay_memory(pattern_table: PatternTable, retention_rate: float) -> None:
    """Apply decay to all per-player frequency counters in-place.

    Multiplies every frequency counter by *retention_rate* for all player
    profiles except the ``__global__`` aggregate profile.
    """
    for player_id, contexts in pattern_table._data.items():
        if player_id == GLOBAL_PROFILE:
            continue
        for _ctx_name, actions in contexts.items():
            for action in actions:
                actions[action] = actions[action] * retention_rate


DEFAULT_MEMORY_PATH: str = "data/watcher_memory.json"


def save_memory(
    pattern_table: PatternTable, path: str = DEFAULT_MEMORY_PATH
) -> None:
    """Serialize a PatternTable to a JSON file.

    Creates parent directories if they do not exist.
    """
    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(json.dumps(pattern_table.to_dict(), indent=2))


def load_memory(path: str = DEFAULT_MEMORY_PATH) -> PatternTable:
    """Load a PatternTable from a JSON file.

    Returns an empty PatternTable if the file does not exist.
    """
    filepath = Path(path)
    if not filepath.exists():
        return PatternTable()
    data = json.loads(filepath.read_text())
    return PatternTable.from_dict(data)


__all__ = [
    "CONTEXTS",
    "CROSS_SESSION_RETENTION",
    "DEFAULT_MEMORY_PATH",
    "GLOBAL_PROFILE",
    "PatternTable",
    "SESSION_RETENTION",
    "decay_memory",
    "load_memory",
    "save_memory",
]
