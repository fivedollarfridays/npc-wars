"""Time-limited lobby: collects players, triggers match after 30s or when full."""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any

from server.queue import enqueue_match, queue_depth

MIN_PLAYERS = 2
MAX_PLAYERS = 8
MIN_HUMANS_FOR_NO_FILL = 4
LOBBY_TIMEOUT = 30.0  # seconds


class Lobby:
    """Collects player submissions and triggers a match."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._players: list[dict[str, Any]] = []
        self._start_time: float | None = None
        self._triggered = False

    def join(self, bot_config: dict[str, Any]) -> bool:
        """Add a player to the lobby. Returns True if accepted. Thread-safe."""
        with self._lock:
            if self._triggered or len(self._players) >= MAX_PLAYERS:
                return False
            self._players.append(bot_config)
            if self._start_time is None:
                self._start_time = time.monotonic()
            if len(self._players) >= MAX_PLAYERS:
                self._trigger_match()
            return True

    def status(self) -> dict[str, Any]:
        """Return lobby status for UI."""
        if self._start_time is None:
            return {
                "players": 0,
                "max": MAX_PLAYERS,
                "time_remaining": None,
                "triggered": False,
            }
        elapsed = time.monotonic() - self._start_time
        remaining = max(0.0, LOBBY_TIMEOUT - elapsed)
        return {
            "players": len(self._players),
            "max": MAX_PLAYERS,
            "time_remaining": round(remaining, 1),
            "triggered": self._triggered,
        }

    def check_timer(self) -> bool:
        """Check if timer expired. Call periodically. Returns True if match triggered."""
        with self._lock:
            if self._triggered or self._start_time is None:
                return False
            if time.monotonic() - self._start_time >= LOBBY_TIMEOUT:
                self._trigger_match()
                return True
            return False

    def reset(self) -> None:
        """Reset lobby for next match."""
        self._players = []
        self._start_time = None
        self._triggered = False

    def _trigger_match(self) -> None:
        if self._triggered:
            return
        self._triggered = True
        bot_configs = list(self._players)
        # Fill to MIN_HUMANS_FOR_NO_FILL (not MAX) to keep matches small for few humans
        if len(bot_configs) < MIN_HUMANS_FOR_NO_FILL:
            bot_configs.extend(
                _get_fill_bots(MIN_HUMANS_FOR_NO_FILL - len(bot_configs))
            )
        match_mode = "extended" if queue_depth() > 3 else "standard"
        job = {
            "job_id": str(uuid.uuid4()),
            "bot_configs": bot_configs,
            "match_id": None,
            "results_dir": "results",
            "match_mode": match_mode,
        }
        enqueue_match(job)


def _get_fill_bots(count: int) -> list[dict[str, Any]]:
    """Return AI fill bots calibrated to a default skill level."""
    from server.fill_bots import generate_fill_bots

    return generate_fill_bots(count, skill_level=0.5)
