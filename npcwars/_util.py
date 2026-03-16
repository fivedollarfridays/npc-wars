"""Shared pure-math utilities for the npcwars helpers DSL.

No engine imports allowed — sandbox-safe.
"""

from __future__ import annotations

__all__ = ["OPPOSITE", "direction_toward", "is_in_storm", "manhattan", "unpack_target"]

OPPOSITE: dict[str, str] = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
}


def direction_toward(from_x: int, from_y: int, to_x: int, to_y: int) -> str:
    """Return the cardinal direction from one position toward another.

    Ties (|dx| == |dy|) are broken by the x-axis.
    Same position returns "north" as an arbitrary safe default.

    NOTE: duplicated in engine/grid.py for import isolation — keep in sync.
    """
    dx = to_x - from_x
    dy = to_y - from_y
    if dx == 0 and dy == 0:
        return "north"
    if abs(dx) >= abs(dy):
        return "east" if dx > 0 else "west"
    return "south" if dy > 0 else "north"


def is_in_storm(x: int, y: int, grid_size: int, storm_border: int) -> bool:
    """Return True if (x, y) is inside the storm border.

    NOTE: duplicated in engine/grid.py for import isolation — keep in sync.
    """
    if storm_border <= 0:
        return False
    return (
        x < storm_border
        or x >= grid_size - storm_border
        or y < storm_border
        or y >= grid_size - storm_border
    )


def manhattan(x1: int, y1: int, x2: int, y2: int) -> int:
    """Manhattan distance between two points."""
    return abs(x1 - x2) + abs(y1 - y2)


def unpack_target(target: dict | tuple) -> tuple[int, int]:
    """Extract (x, y) from an enemy dict or coordinate tuple."""
    if isinstance(target, dict):
        return target["x"], target["y"]
    return target[0], target[1]
