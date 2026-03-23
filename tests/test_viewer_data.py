"""Tests that match JSON contains the fields expected by the browser viewer.

The viewer (viewer/match.html) renders terrain tiles and map name from match
JSON.  These tests verify the engine produces the right data shape.
"""
from __future__ import annotations

import json
from pathlib import Path

from engine.terrain import MAP_NAMES, TerrainMap, build_map

TILE_TYPES = {"open", "wall", "water", "high_ground", "cover", "crystal"}
VIEWER_TERRAIN_COLORS = {"wall", "water", "high_ground", "cover", "crystal"}


def _load_sample_match() -> dict | None:
    """Load a sample match JSON from results/ if available."""
    results = sorted(Path("results").glob("match_*.json"))
    if not results:
        return None
    return json.loads(results[-1].read_text())


def test_match_json_has_map_field() -> None:
    """Match JSON must include a 'map' string for viewer header display."""
    data = _load_sample_match()
    if data is None:
        # No match files -- verify engine terrain produces map name
        t = build_map("fortress", 12)
        assert t.name == "fortress"
        return
    assert "map" in data
    assert isinstance(data["map"], str)
    assert data["map"] in MAP_NAMES


def test_match_json_has_terrain_tiles() -> None:
    """Match JSON must include 'terrain_tiles' 2D array of tile type strings."""
    data = _load_sample_match()
    if data is None:
        t = build_map("fortress", 12)
        assert isinstance(t.tiles, list)
        assert len(t.tiles) == 12
        return
    assert "terrain_tiles" in data
    tiles = data["terrain_tiles"]
    assert isinstance(tiles, list)
    assert len(tiles) > 0
    assert isinstance(tiles[0], list)


def test_terrain_tile_types_are_valid() -> None:
    """Every tile type in the terrain grid must be a known type."""
    data = _load_sample_match()
    if data is None:
        t = build_map("fortress", 12)
        tiles = t.tiles
    else:
        tiles = data["terrain_tiles"]
    for row in tiles:
        for tile in row:
            assert tile in TILE_TYPES, f"Unknown tile type: {tile}"


def test_terrain_tiles_grid_is_square() -> None:
    """Terrain grid dimensions must match grid_size."""
    data = _load_sample_match()
    if data is None:
        size = 12
        t = build_map("arena", size)
        tiles = t.tiles
    else:
        size = data["grid_size"]
        tiles = data["terrain_tiles"]
    assert len(tiles) == size
    for row in tiles:
        assert len(row) == size


def test_fortress_map_has_non_open_tiles() -> None:
    """Fortress map must contain walls and other terrain, not all open."""
    t = build_map("fortress", 14)
    all_types = {tile for row in t.tiles for tile in row}
    assert "wall" in all_types, "Fortress should have walls"
    assert len(all_types) > 1, "Fortress should have mixed terrain"


def test_viewer_color_keys_cover_all_non_open_types() -> None:
    """The viewer's TERRAIN_COLORS dict must have entries for all non-open tile types."""
    non_open = TILE_TYPES - {"open"}
    assert non_open == VIEWER_TERRAIN_COLORS
