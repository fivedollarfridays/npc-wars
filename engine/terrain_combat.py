"""Terrain-based combat modifiers for NPC Wars.

Provides functions to compute to-hit bonuses, AC bonuses, damage
multipliers, line-of-sight checks, and rest-healing eligibility
based on terrain tile types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from engine.terrain import HIGH_GROUND, WALL, WATER, COVER

if TYPE_CHECKING:
    from engine.terrain import TerrainMap

__all__ = [
    "get_terrain_to_hit_mod",
    "get_terrain_ac_mod",
    "get_terrain_damage_mult",
    "has_line_of_sight",
    "can_rest_heal",
]

# ── Constants ────────────────────────────────────────────────────────

HIGH_GROUND_TO_HIT: int = 2
WATER_TO_HIT: int = -2
COVER_AC_BONUS: int = 3
HIGH_GROUND_DAMAGE_MULT: float = 1.15


# ── To-hit modifier ─────────────────────────────────────────────────


def get_terrain_to_hit_mod(terrain: TerrainMap | None, x: int, y: int) -> int:
    """Return attacker to-hit modifier based on the tile they stand on.

    +2 for high_ground, -2 for water, 0 otherwise.
    """
    if terrain is None:
        return 0
    tile = terrain.get_tile(x, y)
    if tile == HIGH_GROUND:
        return HIGH_GROUND_TO_HIT
    if tile == WATER:
        return WATER_TO_HIT
    return 0


# ── AC modifier ──────────────────────────────────────────────────────


def get_terrain_ac_mod(terrain: TerrainMap | None, x: int, y: int) -> int:
    """Return defender AC bonus based on the tile they stand on.

    +3 for cover, 0 otherwise.
    """
    if terrain is None:
        return 0
    if terrain.get_tile(x, y) == COVER:
        return COVER_AC_BONUS
    return 0


# ── Damage multiplier ───────────────────────────────────────────────


def get_terrain_damage_mult(terrain: TerrainMap | None, x: int, y: int) -> float:
    """Return damage multiplier based on the tile the attacker stands on.

    1.15x for high_ground, 1.0 otherwise.
    """
    if terrain is None:
        return 1.0
    if terrain.get_tile(x, y) == HIGH_GROUND:
        return HIGH_GROUND_DAMAGE_MULT
    return 1.0


# ── Line of sight ────────────────────────────────────────────────────


def _bresenham(x1: int, y1: int, x2: int, y2: int) -> list[tuple[int, int]]:
    """Return all grid points on the line from (x1,y1) to (x2,y2).

    Uses Bresenham's line algorithm.  Includes start and end points.
    """
    points: list[tuple[int, int]] = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x2 > x1 else -1
    sy = 1 if y2 > y1 else -1
    err = dx - dy
    cx, cy = x1, y1
    while True:
        points.append((cx, cy))
        if cx == x2 and cy == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            cx += sx
        if e2 < dx:
            err += dx
            cy += sy
    return points


def has_line_of_sight(
    terrain: TerrainMap | None, x1: int, y1: int, x2: int, y2: int,
) -> bool:
    """Return True if no WALL tile blocks the path between two positions.

    Start and end tiles are excluded (you're ON them, not behind them).
    If *terrain* is None, always returns True.
    """
    if terrain is None:
        return True
    points = _bresenham(x1, y1, x2, y2)
    # Skip start and end -- only check intermediate tiles
    for px, py in points[1:-1]:
        if terrain.get_tile(px, py) == WALL:
            return False
    return True


# ── Rest healing eligibility ─────────────────────────────────────────


def can_rest_heal(terrain: TerrainMap | None, x: int, y: int) -> bool:
    """Return True if a bot can heal via rest at (x, y).

    False if standing in water, True otherwise.
    """
    if terrain is None:
        return True
    return terrain.get_tile(x, y) != WATER
