"""Tests for terrain combat modifiers (T37.3)."""

from __future__ import annotations

from engine.terrain import TerrainMap, OPEN, WALL, WATER, HIGH_GROUND, COVER
from engine.terrain_combat import (
    get_terrain_to_hit_mod,
    get_terrain_ac_mod,
    get_terrain_damage_mult,
    has_line_of_sight,
    can_rest_heal,
)


# ── Helpers ──────────────────────────────────────────────────────────


def _make_map(tile: str, size: int = 5) -> TerrainMap:
    """Build a uniform terrain map filled with *tile*."""
    tiles = [[tile] * size for _ in range(size)]
    return TerrainMap("test", size, tiles)


def _make_mixed_map(size: int = 7) -> TerrainMap:
    """Build a 7x7 map with a wall column at x=3 for LoS tests."""
    tiles = [[OPEN] * size for _ in range(size)]
    for y in range(size):
        tiles[y][3] = WALL
    return TerrainMap("los_test", size, tiles)


# ── get_terrain_to_hit_mod ───────────────────────────────────────────


def test_to_hit_high_ground_gives_plus_2() -> None:
    tm = _make_map(HIGH_GROUND)
    assert get_terrain_to_hit_mod(tm, 2, 2) == 2


def test_to_hit_water_gives_minus_2() -> None:
    tm = _make_map(WATER)
    assert get_terrain_to_hit_mod(tm, 2, 2) == -2


def test_to_hit_open_gives_0() -> None:
    tm = _make_map(OPEN)
    assert get_terrain_to_hit_mod(tm, 2, 2) == 0


def test_to_hit_none_terrain_gives_0() -> None:
    assert get_terrain_to_hit_mod(None, 2, 2) == 0


# ── get_terrain_ac_mod ───────────────────────────────────────────────


def test_ac_cover_gives_plus_3() -> None:
    tm = _make_map(COVER)
    assert get_terrain_ac_mod(tm, 2, 2) == 3


def test_ac_open_gives_0() -> None:
    tm = _make_map(OPEN)
    assert get_terrain_ac_mod(tm, 2, 2) == 0


def test_ac_none_terrain_gives_0() -> None:
    assert get_terrain_ac_mod(None, 2, 2) == 0


# ── get_terrain_damage_mult ──────────────────────────────────────────


def test_damage_mult_high_ground_gives_1_15() -> None:
    tm = _make_map(HIGH_GROUND)
    assert get_terrain_damage_mult(tm, 2, 2) == 1.15


def test_damage_mult_open_gives_1_0() -> None:
    tm = _make_map(OPEN)
    assert get_terrain_damage_mult(tm, 2, 2) == 1.0


def test_damage_mult_none_terrain_gives_1_0() -> None:
    assert get_terrain_damage_mult(None, 2, 2) == 1.0


# ── has_line_of_sight ────────────────────────────────────────────────


def test_los_open_path_succeeds() -> None:
    tm = _make_map(OPEN)
    assert has_line_of_sight(tm, 0, 0, 4, 0) is True


def test_los_wall_blocks() -> None:
    """Wall column at x=3 blocks LoS from x=0 to x=6."""
    tm = _make_mixed_map()
    assert has_line_of_sight(tm, 0, 3, 6, 3) is False


def test_los_none_terrain_always_true() -> None:
    assert has_line_of_sight(None, 0, 0, 5, 5) is True


def test_los_start_end_wall_not_blocked() -> None:
    """Standing ON a wall tile doesn't block your own LoS."""
    tiles = [[OPEN] * 5 for _ in range(5)]
    tiles[0][0] = WALL  # start tile
    tiles[0][4] = WALL  # end tile
    tm = TerrainMap("edge_test", 5, tiles)
    assert has_line_of_sight(tm, 0, 0, 4, 0) is True


def test_los_adjacent_always_true() -> None:
    """Adjacent tiles (distance 1) always have LoS — no intermediate tiles."""
    tm = _make_map(WALL)
    assert has_line_of_sight(tm, 2, 2, 3, 2) is True


# ── can_rest_heal ────────────────────────────────────────────────────


def test_rest_heal_water_blocked() -> None:
    tm = _make_map(WATER)
    assert can_rest_heal(tm, 2, 2) is False


def test_rest_heal_open_allowed() -> None:
    tm = _make_map(OPEN)
    assert can_rest_heal(tm, 2, 2) is True


def test_rest_heal_none_terrain_allowed() -> None:
    assert can_rest_heal(None, 2, 2) is True
