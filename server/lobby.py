"""Time-limited lobby: collects players, triggers match after 30s or when full."""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
import time
import uuid
from typing import Any

from server.queue import enqueue_match, is_in_memory_mode, queue_depth

_logger = logging.getLogger(__name__)

MIN_PLAYERS = 2
MAX_PLAYERS = 8
MIN_HUMANS_FOR_NO_FILL = 4
LOBBY_TIMEOUT = 30.0  # seconds


def _inline_on_no_redis_enabled() -> bool:
    """Opt-in flag for inline match execution when Redis is unavailable.

    Default False: production and tests use the queue path regardless of backend.
    Set LOBBY_INLINE_ON_NO_REDIS=1 (or true/yes) for local dev without Redis.
    """
    return os.environ.get("LOBBY_INLINE_ON_NO_REDIS", "").strip().lower() in {
        "1", "true", "yes", "on",
    }


class Lobby:
    """Collects player submissions and triggers a match."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._players: list[dict[str, Any]] = []
        self._start_time: float | None = None
        self._triggered = False
        self._match_id: str | None = None

    def join(
        self,
        bot_config: dict[str, Any],
        conn: sqlite3.Connection | None = None,
    ) -> bool:
        """Add a player to the lobby. Returns True if accepted. Thread-safe."""
        with self._lock:
            if self._triggered or len(self._players) >= MAX_PLAYERS:
                return False
            self._players.append(bot_config)
            if self._start_time is None:
                self._start_time = time.monotonic()
            if len(self._players) >= MAX_PLAYERS:
                self._trigger_match(conn=conn)
            return True

    def status(self) -> dict[str, Any]:
        """Return lobby status for UI. Thread-safe."""
        with self._lock:
            player_list = [
                {"emoji": p.get("emoji", "?"), "name": p.get("name", "Unknown")}
                for p in self._players
            ]
            if self._start_time is None:
                return {
                    "players": 0,
                    "max": MAX_PLAYERS,
                    "time_remaining": None,
                    "triggered": False,
                    "player_list": player_list,
                    "match_id": self._match_id,
                    "status": self._lobby_status(),
                }
            elapsed = time.monotonic() - self._start_time
            remaining = max(0.0, LOBBY_TIMEOUT - elapsed)
            return {
                "players": len(self._players),
                "max": MAX_PLAYERS,
                "time_remaining": round(remaining, 1),
                "triggered": self._triggered,
                "player_list": player_list,
                "match_id": self._match_id,
                "status": self._lobby_status(),
            }

    def check_timer(
        self, conn: sqlite3.Connection | None = None
    ) -> bool:
        """Check if timer expired. Call periodically. Returns True if match triggered."""
        with self._lock:
            if self._triggered or self._start_time is None:
                return False
            if time.monotonic() - self._start_time >= LOBBY_TIMEOUT:
                self._trigger_match(conn=conn)
                return True
            return False

    def _lobby_status(self) -> str:
        """Derive lobby status string from internal state."""
        if self._triggered:
            if self._match_id:
                return "running"
            return "complete"
        if not self._players:
            return "waiting"
        return "filling"

    def reset(self) -> None:
        """Reset lobby for next match."""
        self._players = []
        self._start_time = None
        self._triggered = False
        self._match_id = None

    def _trigger_match(
        self, conn: sqlite3.Connection | None = None
    ) -> None:
        if self._triggered:
            return
        self._match_id = str(uuid.uuid4())
        self._triggered = True
        bot_configs = list(self._players)
        # Fill to MIN_HUMANS_FOR_NO_FILL (not MAX) to keep matches small
        fill_needed = max(0, MIN_HUMANS_FOR_NO_FILL - len(bot_configs))
        if fill_needed > 0:
            rival = _maybe_inject_rival(bot_configs, conn)
            if rival:
                fill_needed -= 1
                bot_configs.append(rival)
            if fill_needed > 0:
                bot_configs.extend(_get_fill_bots(fill_needed))
        match_mode = "extended" if queue_depth() > 3 else "standard"
        job = {
            "job_id": str(uuid.uuid4()),
            "bot_configs": bot_configs,
            "match_id": self._match_id,
            "results_dir": "results",
            "match_mode": match_mode,
        }
        if _inline_on_no_redis_enabled() and is_in_memory_mode():
            _run_match_inline(job)
        else:
            enqueue_match(job)


def _run_match_inline(job: dict) -> None:
    """Opt-in inline match processing for local dev without Redis.

    Only runs when LOBBY_INLINE_ON_NO_REDIS is truthy AND the queue backend
    is the in-memory fallback. Errors are logged structurally; callers do not
    receive exceptions. Production paths use enqueue_match instead.
    """

    def _process() -> None:
        from engine.game import run_match
        from engine.match_writer import write_match

        try:
            match_data = run_match(
                job["bot_configs"],
                match_id=job["match_id"],
                seed=job.get("seed"),
            )
            write_match(match_data, job.get("results_dir", "results"))
            _logger.info("Inline match %s completed", job.get("match_id"))
        except Exception as exc:
            _logger.error("Inline match %s failed: %s", job.get("match_id"), exc)

    thread = threading.Thread(target=_process, daemon=True)
    thread.start()


def _maybe_inject_rival(
    bot_configs: list[dict[str, Any]],
    conn: sqlite3.Connection | None,
) -> dict[str, Any] | None:
    """Return a rival config if any human has an uncleared rival tier."""
    if conn is None:
        return None

    from server.rival_db import (
        WINS_TO_ADVANCE,
        ensure_rival_progress,
    )
    from server.rival_factory import MAX_TIER, generate_rival

    for cfg in bot_configs:
        player_id = cfg.get("player_id")
        if not player_id:
            continue
        progress = ensure_rival_progress(conn, player_id)
        tier = progress["current_tier"]
        # Skip if player has cleared the final tier
        if tier >= MAX_TIER and progress["wins"] >= WINS_TO_ADVANCE:
            continue
        # Tier 5 loads full patterns + accuracy cap
        if tier == 5:
            return _generate_mirror_rival(player_id, conn)
        # Tier 4 loads player patterns for counter-play
        if tier == 4:
            return _generate_counter_rival(player_id)
        return generate_rival(tier)
    return None


def _generate_counter_rival(player_id: str) -> dict[str, Any]:
    """Generate a Tier 4 Counter rival with embedded pattern data."""
    from server.rival_factory import generate_rival
    from server.rival_patterns import (
        compact_for_embed,
        get_pattern_summary,
        load_player_patterns,
    )

    table = load_player_patterns(player_id)
    summary = get_pattern_summary(table, player_id)
    embed_data = compact_for_embed(summary)
    return generate_rival(4, pattern_data=embed_data)


def _generate_mirror_rival(
    player_id: str, conn: sqlite3.Connection | None,
) -> dict[str, Any]:
    """Generate Mirror rival with full pattern data + accuracy cap."""
    from engine.watcher_brain import HumanPerformance, get_accuracy_cap
    from server.rival_factory import generate_rival
    from server.rival_patterns import (
        compact_for_embed,
        get_pattern_summary,
        load_player_patterns,
    )

    table = load_player_patterns(player_id)
    summary = get_pattern_summary(table, player_id)
    embed_data = compact_for_embed(summary)

    performance = HumanPerformance(hp_ratio=0.5, kills=1, rounds_survived=20)
    cap = get_accuracy_cap(performance)

    if not embed_data:
        return generate_rival(5)
    return generate_rival(5, pattern_data=embed_data, accuracy_cap=cap)


def _get_fill_bots(count: int) -> list[dict[str, Any]]:
    """Return AI fill bots calibrated to a default skill level."""
    from server.fill_bots import generate_fill_bots

    return generate_fill_bots(count, skill_level=0.5)
