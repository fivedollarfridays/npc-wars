"""Terrain map definitions and data model for NPC Wars."""

from __future__ import annotations

import random
from collections.abc import Callable

__all__ = [
    "OPEN", "WALL", "WATER", "HIGH_GROUND", "COVER", "CRYSTAL",
    "TILE_CHARS", "TerrainMap", "MAP_NAMES", "build_map", "get_random_map",
]

# ── Tile type constants ──────────────────────────────────────────────

OPEN = "open"
WALL = "wall"
WATER = "water"
HIGH_GROUND = "high_ground"
COVER = "cover"
CRYSTAL = "crystal"

TILE_CHARS: dict[str, str] = {
    OPEN: ".",
    WALL: "#",
    WATER: "~",
    HIGH_GROUND: "^",
    COVER: "%",
    CRYSTAL: "*",
}

# ── TerrainMap data model ────────────────────────────────────────────


class TerrainMap:
    """Grid of tile types with query helpers."""

    def __init__(self, name: str, grid_size: int, tiles: list[list[str]]) -> None:
        self.name = name
        self.grid_size = grid_size
        self.tiles = tiles  # tiles[y][x]

    def get_tile(self, x: int, y: int) -> str:
        """Return tile type at (x, y), or WALL if out of bounds."""
        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            return self.tiles[y][x]
        return WALL

    def is_walkable(self, x: int, y: int) -> bool:
        """Return True if the tile at (x, y) is not a wall."""
        return self.get_tile(x, y) != WALL

    def get_tiles_of_type(self, tile_type: str) -> list[tuple[int, int]]:
        """Return all (x, y) positions matching *tile_type*."""
        result: list[tuple[int, int]] = []
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                if self.tiles[y][x] == tile_type:
                    result.append((x, y))
        return result


# ── Map names ────────────────────────────────────────────────────────

MAP_NAMES: tuple[str, ...] = ("arena", "fortress", "highlands", "maze", "storm_pit")


# ── Map builders (private) ───────────────────────────────────────────


def _open_grid(grid_size: int) -> list[list[str]]:
    """Return a grid_size x grid_size grid of OPEN tiles."""
    return [[OPEN] * grid_size for _ in range(grid_size)]


def _build_arena(grid_size: int) -> TerrainMap:
    """All open tiles -- backward-compatible default."""
    return TerrainMap("arena", grid_size, _open_grid(grid_size))


def _build_storm_pit(grid_size: int) -> TerrainMap:
    """All open tiles (fast storm via match mode, not terrain)."""
    return TerrainMap("storm_pit", grid_size, _open_grid(grid_size))


def _build_fortress(grid_size: int) -> TerrainMap:
    """Central cross walls with 4 corridor gaps at cardinal directions."""
    tiles = _open_grid(grid_size)
    mid = grid_size // 2

    # Horizontal wall through center
    for x in range(grid_size):
        tiles[mid][x] = WALL
    # Vertical wall through center
    for y in range(grid_size):
        tiles[y][mid] = WALL

    # Open 2-tile gaps at cardinal directions (corridors)
    gap = max(1, grid_size // 5)
    # North gap (top of vertical line)
    for dy in range(gap):
        tiles[dy][mid] = OPEN
    # South gap (bottom of vertical line)
    for dy in range(gap):
        tiles[grid_size - 1 - dy][mid] = OPEN
    # West gap (left of horizontal line)
    for dx in range(gap):
        tiles[mid][dx] = OPEN
    # East gap (right of horizontal line)
    for dx in range(gap):
        tiles[mid][grid_size - 1 - dx] = OPEN

    # Crystals in corners (2-4)
    corners = [(1, 1), (grid_size - 2, 1),
               (1, grid_size - 2), (grid_size - 2, grid_size - 2)]
    for cx, cy in corners[:4]:
        tiles[cy][cx] = CRYSTAL

    # Cover near corridors
    _place_cover_near_walls(tiles, grid_size, count=6)

    return TerrainMap("fortress", grid_size, tiles)


def _place_cover_near_walls(
    tiles: list[list[str]], grid_size: int, count: int,
) -> None:
    """Place *count* cover tiles adjacent to wall tiles on open squares."""
    placed = 0
    mid = grid_size // 2
    offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for dy, dx in offsets:
        ny, nx = mid + dy, mid + dx
        if 0 <= ny < grid_size and 0 <= nx < grid_size and tiles[ny][nx] == OPEN:
            tiles[ny][nx] = COVER
            placed += 1
            if placed >= count:
                return
    # Additional cover near corridor ends
    gap = max(1, grid_size // 5)
    extra_spots = [
        (mid - 1, gap), (mid + 1, gap),
        (mid - 1, grid_size - 1 - gap), (mid + 1, grid_size - 1 - gap),
    ]
    for ny, nx in extra_spots:
        if placed >= count:
            return
        if 0 <= ny < grid_size and 0 <= nx < grid_size and tiles[ny][nx] == OPEN:
            tiles[ny][nx] = COVER
            placed += 1


def _build_highlands(grid_size: int) -> TerrainMap:
    """Center high_ground, bottom water rows, scattered cover."""
    tiles = _open_grid(grid_size)

    # Center high_ground -- ~30% of each axis
    hg_size = max(3, int(grid_size * 0.3))
    start = (grid_size - hg_size) // 2
    for y in range(start, start + hg_size):
        for x in range(start, start + hg_size):
            tiles[y][x] = HIGH_GROUND

    # Bottom 2 rows are water
    water_rows = max(2, grid_size // 5)
    for y in range(grid_size - water_rows, grid_size):
        for x in range(grid_size):
            tiles[y][x] = WATER

    # Cover tiles near high_ground edges (4 tiles)
    cover_spots = [
        (start - 1, start), (start - 1, start + hg_size - 1),
        (start + hg_size, start), (start + hg_size, start + hg_size - 1),
    ]
    for cy, cx in cover_spots:
        if 0 <= cy < grid_size and 0 <= cx < grid_size and tiles[cy][cx] == OPEN:
            tiles[cy][cx] = COVER

    return TerrainMap("highlands", grid_size, tiles)


def _build_maze(grid_size: int) -> TerrainMap:
    """Wall grid every 3 tiles with 1-tile gaps. Crystals at dead ends."""
    tiles = _open_grid(grid_size)

    # Walls every 3rd column and row, with gaps
    for y in range(grid_size):
        for x in range(grid_size):
            if x % 3 == 0 and y % 3 == 0:
                continue  # intersection stays open (gap)
            if x % 3 == 0 or y % 3 == 0:
                # Wall on grid lines, but skip some for gaps
                if x % 3 == 0 and y % 3 != 0 and y % 6 == 0:
                    continue  # gap in vertical wall
                if y % 3 == 0 and x % 3 != 0 and x % 6 == 0:
                    continue  # gap in horizontal wall
                tiles[y][x] = WALL

    # Crystals at corners (dead-end-like positions)
    crystal_spots = [
        (1, 1), (grid_size - 2, 1),
        (1, grid_size - 2), (grid_size - 2, grid_size - 2),
    ]
    for cx, cy in crystal_spots:
        if 0 <= cy < grid_size and 0 <= cx < grid_size:
            tiles[cy][cx] = CRYSTAL

    return TerrainMap("maze", grid_size, tiles)


# ── Public API ───────────────────────────────────────────────────────

_BUILDERS: dict[str, Callable[[int], TerrainMap]] = {
    "arena": _build_arena,
    "fortress": _build_fortress,
    "highlands": _build_highlands,
    "maze": _build_maze,
    "storm_pit": _build_storm_pit,
}


def build_map(name: str, grid_size: int) -> TerrainMap:
    """Build a named terrain map at the given *grid_size*."""
    builder = _BUILDERS.get(name)
    if builder is None:
        raise ValueError(f"Unknown map name: {name!r}. Choose from {MAP_NAMES}")
    return builder(grid_size)


def get_random_map(rng: random.Random) -> str:
    """Return a random map name from MAP_NAMES."""
    return rng.choice(MAP_NAMES)
