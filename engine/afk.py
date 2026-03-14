"""AFK detection and bot fallback for human players.

Tracks consecutive missed inputs per human player. After AFK_THRESHOLD
consecutive misses the player is marked AFK. After KICK_THRESHOLD
consecutive misses the player is kicked and their adapter is detached.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["AFKTracker", "AFK_THRESHOLD", "KICK_THRESHOLD"]

AFK_THRESHOLD: int = 3
KICK_THRESHOLD: int = 10


@dataclass
class _PlayerState:
    consecutive_misses: int = 0
    afk: bool = False
    kicked: bool = False


class AFKTracker:
    """Tracks consecutive missed inputs for human players."""

    def __init__(self) -> None:
        self._players: dict[str, _PlayerState] = {}

    def register(self, emoji: str) -> None:
        """Add a human player to tracking."""
        self._players[emoji] = _PlayerState()

    def record_miss(self, emoji: str) -> None:
        """Record a missed input for a player."""
        entry = self._players[emoji]
        entry.consecutive_misses += 1
        if entry.consecutive_misses >= KICK_THRESHOLD:
            entry.kicked = True
            entry.afk = True
        elif entry.consecutive_misses >= AFK_THRESHOLD:
            entry.afk = True

    def record_input(self, emoji: str) -> None:
        """Record a successful input, resetting the miss counter."""
        entry = self._players[emoji]
        if entry.kicked:
            return
        entry.consecutive_misses = 0
        entry.afk = False

    def is_afk(self, emoji: str) -> bool:
        """Return True if the player has 3+ consecutive misses."""
        return self._players[emoji].afk

    def is_kicked(self, emoji: str) -> bool:
        """Return True if the player has 10+ consecutive misses."""
        return self._players[emoji].kicked

    def get_status(self, emoji: str) -> dict[str, bool | int]:
        """Return a copy of the player's tracking status."""
        entry = self._players[emoji]
        return {
            "afk": entry.afk,
            "kicked": entry.kicked,
            "consecutive_misses": entry.consecutive_misses,
        }
