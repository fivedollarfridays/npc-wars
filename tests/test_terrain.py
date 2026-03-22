"""Tests for engine/terrain.py — terrain map definitions and data model."""

import random

import pytest


# ── Cycle 1: Tile constants + TerrainMap basics ──────────────────────

def test_tile_type_constants_exist():
    from engine.terrain import OPEN, WALL, WATER, HIGH_GROUND, COVER, CRYSTAL
    assert OPEN == "open"
    assert WALL == "wall"
    assert WATER == "water"
    assert HIGH_GROUND == "high_ground"
    assert COVER == "cover"
    assert CRYSTAL == "crystal"


def test_tile_chars_mapping():
    from engine.terrain import TILE_CHARS, OPEN, WALL, WATER, HIGH_GROUND, COVER, CRYSTAL
    assert TILE_CHARS[OPEN] == "."
    assert TILE_CHARS[WALL] == "#"
    assert TILE_CHARS[WATER] == "~"
    assert TILE_CHARS[HIGH_GROUND] == "^"
    assert TILE_CHARS[COVER] == "%"
    assert TILE_CHARS[CRYSTAL] == "*"


def test_terrain_map_get_tile():
    from engine.terrain import TerrainMap, OPEN, WALL
    tiles = [
        [OPEN, WALL],
        [WALL, OPEN],
    ]
    tm = TerrainMap("test", 2, tiles)
    assert tm.get_tile(0, 0) == OPEN
    assert tm.get_tile(1, 0) == WALL
    assert tm.get_tile(0, 1) == WALL
    assert tm.get_tile(1, 1) == OPEN


def test_terrain_map_out_of_bounds_returns_wall():
    from engine.terrain import TerrainMap, OPEN, WALL
    tiles = [[OPEN]]
    tm = TerrainMap("test", 1, tiles)
    assert tm.get_tile(-1, 0) == WALL
    assert tm.get_tile(0, -1) == WALL
    assert tm.get_tile(1, 0) == WALL
    assert tm.get_tile(0, 1) == WALL


def test_is_walkable_true_for_non_wall():
    from engine.terrain import TerrainMap, OPEN, WATER, HIGH_GROUND, COVER, CRYSTAL
    tiles = [[OPEN, WATER, HIGH_GROUND, COVER, CRYSTAL]]
    tm = TerrainMap("test", 5, tiles)
    for x in range(5):
        assert tm.is_walkable(x, 0) is True


def test_is_walkable_false_for_wall():
    from engine.terrain import TerrainMap, WALL
    tiles = [[WALL]]
    tm = TerrainMap("test", 1, tiles)
    assert tm.is_walkable(0, 0) is False


def test_is_walkable_false_for_out_of_bounds():
    from engine.terrain import TerrainMap, OPEN
    tiles = [[OPEN]]
    tm = TerrainMap("test", 1, tiles)
    assert tm.is_walkable(-1, 0) is False
    assert tm.is_walkable(5, 5) is False


# ── Cycle 2: get_tiles_of_type ───────────────────────────────────────

def test_get_tiles_of_type_finds_correct_positions():
    from engine.terrain import TerrainMap, OPEN, WALL
    tiles = [
        [OPEN, WALL, OPEN],
        [WALL, OPEN, WALL],
        [OPEN, WALL, OPEN],
    ]
    tm = TerrainMap("test", 3, tiles)
    walls = tm.get_tiles_of_type(WALL)
    assert set(walls) == {(1, 0), (0, 1), (2, 1), (1, 2)}
    opens = tm.get_tiles_of_type(OPEN)
    assert set(opens) == {(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)}


def test_get_tiles_of_type_empty_result():
    from engine.terrain import TerrainMap, OPEN, CRYSTAL
    tiles = [[OPEN, OPEN], [OPEN, OPEN]]
    tm = TerrainMap("test", 2, tiles)
    assert tm.get_tiles_of_type(CRYSTAL) == []


# ── Cycle 3: Arena + Storm Pit builders ──────────────────────────────

def test_arena_all_open():
    from engine.terrain import build_map, OPEN
    tm = build_map("arena", 10)
    assert tm.name == "arena"
    assert tm.grid_size == 10
    for y in range(10):
        for x in range(10):
            assert tm.get_tile(x, y) == OPEN


def test_storm_pit_all_open():
    from engine.terrain import build_map, OPEN
    tm = build_map("storm_pit", 10)
    assert tm.name == "storm_pit"
    for y in range(10):
        for x in range(10):
            assert tm.get_tile(x, y) == OPEN


# ── Cycle 4: Fortress builder ────────────────────────────────────────

def test_fortress_has_walls():
    from engine.terrain import build_map, WALL
    tm = build_map("fortress", 10)
    walls = tm.get_tiles_of_type(WALL)
    assert len(walls) > 0, "Fortress must have wall tiles"


def test_fortress_has_open_corridors():
    from engine.terrain import build_map, WALL
    tm = build_map("fortress", 10)
    mid = 10 // 2
    # At least one cardinal edge of the cross should be open (corridor)
    assert tm.get_tile(mid, 0) != WALL, "North corridor should be open"
    assert tm.get_tile(mid, 9) != WALL, "South corridor should be open"
    assert tm.get_tile(0, mid) != WALL, "West corridor should be open"
    assert tm.get_tile(9, mid) != WALL, "East corridor should be open"


def test_fortress_has_crystals():
    from engine.terrain import build_map, CRYSTAL
    tm = build_map("fortress", 10)
    crystals = tm.get_tiles_of_type(CRYSTAL)
    assert 2 <= len(crystals) <= 4


# ── Cycle 5: Highlands builder ───────────────────────────────────────

def test_highlands_has_high_ground():
    from engine.terrain import build_map, HIGH_GROUND
    tm = build_map("highlands", 10)
    hg = tm.get_tiles_of_type(HIGH_GROUND)
    assert len(hg) >= 9, "Highlands should have at least 3x3 high_ground"


def test_highlands_has_water():
    from engine.terrain import build_map, WATER
    tm = build_map("highlands", 10)
    water = tm.get_tiles_of_type(WATER)
    assert len(water) > 0, "Highlands must have water tiles"


def test_highlands_has_cover():
    from engine.terrain import build_map, COVER
    tm = build_map("highlands", 10)
    cover = tm.get_tiles_of_type(COVER)
    assert len(cover) > 0, "Highlands must have cover tiles"


# ── Cycle 6: Maze builder ────────────────────────────────────────────

def test_maze_has_wall_grid():
    from engine.terrain import build_map, WALL
    tm = build_map("maze", 10)
    walls = tm.get_tiles_of_type(WALL)
    assert len(walls) > 0, "Maze must have walls"
    # Roughly 25% walls
    total = 10 * 10
    wall_pct = len(walls) / total
    assert 0.10 < wall_pct < 0.50, f"Expected ~25% walls, got {wall_pct:.0%}"


def test_maze_has_crystals():
    from engine.terrain import build_map, CRYSTAL
    tm = build_map("maze", 10)
    crystals = tm.get_tiles_of_type(CRYSTAL)
    assert 2 <= len(crystals) <= 4


# ── Cycle 7: Scaling to different grid sizes ─────────────────────────

@pytest.mark.parametrize("grid_size", [10, 12, 15])
def test_all_maps_build_at_various_sizes(grid_size):
    from engine.terrain import build_map, MAP_NAMES
    for name in MAP_NAMES:
        tm = build_map(name, grid_size)
        assert tm.grid_size == grid_size
        assert len(tm.tiles) == grid_size
        assert all(len(row) == grid_size for row in tm.tiles)


@pytest.mark.parametrize("grid_size", [10, 12, 15])
def test_crystal_count_2_to_4_for_non_arena_maps(grid_size):
    from engine.terrain import build_map, CRYSTAL
    for name in ("fortress", "maze"):
        tm = build_map(name, grid_size)
        crystals = tm.get_tiles_of_type(CRYSTAL)
        assert 2 <= len(crystals) <= 4, (
            f"{name} at size {grid_size}: expected 2-4 crystals, got {len(crystals)}"
        )


# ── Cycle 8: Public API ─────────────────────────────────────────────

def test_build_map_unknown_name_raises():
    from engine.terrain import build_map
    with pytest.raises(ValueError, match="Unknown map name"):
        build_map("nonexistent", 10)


def test_get_random_map_returns_valid_name():
    from engine.terrain import get_random_map, MAP_NAMES
    rng = random.Random(42)
    for _ in range(20):
        name = get_random_map(rng)
        assert name in MAP_NAMES


def test_map_names_tuple():
    from engine.terrain import MAP_NAMES
    assert MAP_NAMES == ("arena", "fortress", "highlands", "maze", "storm_pit")
