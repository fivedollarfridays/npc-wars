"""Cringe spawn conditions and mid-match entry logic."""

from __future__ import annotations

import logging
import random
from typing import Any

from engine.grid import is_in_storm, is_valid_position

log = logging.getLogger(__name__)

__all__ = ["check_watcher_spawn", "find_spawn_position", "build_spawn_event"]

# Spawn thresholds
_MIN_ROUNDS_SURVIVED = 5
_MIN_HP_RATIO = 0.50  # strictly greater than 50%
_MIN_SPAWN_DISTANCE = 3
_MAX_RANDOM_ATTEMPTS = 1000


def check_watcher_spawn(
    bots: list[Any],
    round_num: int,
    watcher_present: bool,
) -> bool:
    """Check if The Cringe should spawn this round.

    Returns True if:
    - At least one alive human bot is present (has human_adapter)
    - Watcher is not already present
    - Any alive human survived 5+ rounds with >50% HP, OR any alive human has kills > 0
    """
    if watcher_present:
        return False

    humans = [b for b in bots if getattr(b, "human_adapter", None) is not None and b.alive]
    if not humans:
        return False

    for h in humans:
        if h.kills > 0:
            return True
        if h.rounds_survived >= _MIN_ROUNDS_SURVIVED and h.hp > h.derived.max_hp * _MIN_HP_RATIO:
            return True

    return False


def find_spawn_position(
    grid_size: int,
    storm_border: int,
    occupied: set[tuple[int, int]],
    human_positions: list[tuple[int, int]],
    rng: random.Random,
) -> tuple[int, int]:
    """Find a valid spawn tile 3+ Manhattan distance from any human.

    Tries random positions up to 1000 attempts.
    Falls back to any unoccupied valid position if 3+ distance impossible.
    """
    def _is_valid(x: int, y: int) -> bool:
        return (
            is_valid_position(x, y, grid_size)
            and not is_in_storm(x, y, grid_size, storm_border)
            and (x, y) not in occupied
        )

    def _far_enough(x: int, y: int) -> bool:
        return all(
            abs(x - hx) + abs(y - hy) >= _MIN_SPAWN_DISTANCE
            for hx, hy in human_positions
        )

    # Primary: find a valid position 3+ away from humans
    for _ in range(_MAX_RANDOM_ATTEMPTS):
        x = rng.randint(0, grid_size - 1)
        y = rng.randint(0, grid_size - 1)
        if _is_valid(x, y) and _far_enough(x, y):
            return (x, y)

    # Fallback: any valid unoccupied position
    for _ in range(_MAX_RANDOM_ATTEMPTS):
        x = rng.randint(0, grid_size - 1)
        y = rng.randint(0, grid_size - 1)
        if _is_valid(x, y):
            return (x, y)

    # Last resort: scan entire grid
    for x in range(grid_size):
        for y in range(grid_size):
            if _is_valid(x, y):
                return (x, y)

    log.warning("No valid spawn position found on %dx%d grid", grid_size, grid_size)
    return (0, 0)


def build_spawn_event(x: int, y: int) -> dict[str, Any]:
    """Return a watcher_spawn event dict."""
    return {"type": "watcher_spawn", "x": x, "y": y}
