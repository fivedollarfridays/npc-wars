"""Tests for terrain-aware movement: walls, water, crystals, spawning."""

from __future__ import annotations

from engine.combat import Bot
from engine.terrain import CRYSTAL, OPEN, WALL, WATER, TerrainMap
from engine.rounds import resolve_movement
from engine.grid import spawn_positions

import random


def _make_bot(emoji: str, x: int, y: int) -> Bot:
    """Create a minimal Bot for movement tests."""
    return Bot(
        name=f"bot_{emoji}", emoji=emoji, bio="test",
        author="test", decide_func=lambda s: ("rest",),
        x=x, y=y,
    )


def _simple_terrain(grid_size: int = 10, overrides: dict[tuple[int, int], str] | None = None) -> TerrainMap:
    """Build an all-OPEN terrain with optional tile overrides."""
    tiles = [[OPEN] * grid_size for _ in range(grid_size)]
    for (x, y), tile_type in (overrides or {}).items():
        tiles[y][x] = tile_type
    return TerrainMap("test_map", grid_size, tiles)


# ── Cycle 1: Wall blocks move + backward compat ────────────────────


def test_wall_blocks_move() -> None:
    """Bot trying to move into a wall stays put and generates wall_blocked event."""
    terrain = _simple_terrain(10, {(5, 4): WALL})
    bot = _make_bot("A", x=5, y=5)
    actions: dict[str, tuple[str, ...]] = {"A": ("move", "north")}

    events = resolve_movement([bot], actions, 10, terrain=terrain)

    assert bot.x == 5
    assert bot.y == 5
    wall_events = [e for e in events if e.get("type") == "wall_blocked"]
    assert len(wall_events) == 1
    assert wall_events[0]["emoji"] == "A"


def test_movement_without_terrain_backward_compat() -> None:
    """Movement works as before when terrain is None."""
    bot = _make_bot("A", x=5, y=5)
    actions: dict[str, tuple[str, ...]] = {"A": ("move", "north")}

    resolve_movement([bot], actions, 10, terrain=None)

    assert bot.x == 5
    assert bot.y == 4  # moved north


def test_move_into_open_tile_with_terrain() -> None:
    """Move into open tile succeeds even with terrain present."""
    terrain = _simple_terrain(10)
    bot = _make_bot("A", x=5, y=5)
    actions: dict[str, tuple[str, ...]] = {"A": ("move", "north")}

    resolve_movement([bot], actions, 10, terrain=terrain)

    assert bot.x == 5
    assert bot.y == 4


# ── Cycle 2: Wall blocks dash ──────────────────────────────────────


def test_wall_blocks_dash_intermediate() -> None:
    """Dash blocked when the intermediate tile is a wall."""
    terrain = _simple_terrain(10, {(5, 4): WALL})
    bot = _make_bot("A", x=5, y=5)
    actions: dict[str, tuple[str, ...]] = {"A": ("dash", "north")}

    events = resolve_movement([bot], actions, 10, terrain=terrain)

    assert bot.x == 5
    assert bot.y == 5  # didn't move
    wall_events = [e for e in events if e.get("type") == "wall_blocked"]
    assert len(wall_events) == 1


def test_wall_blocks_dash_destination_lands_on_intermediate() -> None:
    """Dash destination is wall but intermediate is clear -- bot lands on intermediate."""
    terrain = _simple_terrain(10, {(5, 3): WALL})
    bot = _make_bot("A", x=5, y=5)
    actions: dict[str, tuple[str, ...]] = {"A": ("dash", "north")}

    events = resolve_movement([bot], actions, 10, terrain=terrain)

    assert bot.x == 5
    assert bot.y == 4  # landed on intermediate
    dash_events = [e for e in events if e.get("type") == "dash"]
    assert len(dash_events) == 1
    assert dash_events[0]["to_y"] == 4


# ── Cycle 3: Water tile ────────────────────────────────────────────


def test_water_tile_allows_movement() -> None:
    """Bot can move onto water tile (it is walkable)."""
    terrain = _simple_terrain(10, {(5, 4): WATER})
    bot = _make_bot("A", x=5, y=5)
    actions: dict[str, tuple[str, ...]] = {"A": ("move", "north")}

    resolve_movement([bot], actions, 10, terrain=terrain)

    assert bot.x == 5
    assert bot.y == 4  # moved successfully


def test_water_tile_extra_energy_cost() -> None:
    """Moving onto water costs 5 extra energy and generates water_penalty event."""
    terrain = _simple_terrain(10, {(5, 4): WATER})
    bot = _make_bot("A", x=5, y=5)
    initial_energy = bot.energy
    actions: dict[str, tuple[str, ...]] = {"A": ("move", "north")}

    events = resolve_movement([bot], actions, 10, terrain=terrain)

    assert bot.energy == initial_energy - 5
    water_events = [e for e in events if e.get("type") == "water_penalty"]
    assert len(water_events) == 1
    assert water_events[0]["cost"] == 5


# ── Cycle 4: Crystal pickup ────────────────────────────────────────


def test_crystal_grants_energy_on_first_step() -> None:
    """First bot stepping on crystal gets +10 energy."""
    terrain = _simple_terrain(10, {(5, 4): CRYSTAL})
    bot = _make_bot("A", x=5, y=5)
    # Drain some energy so the bonus is visible
    bot.energy = 50
    collected: set[tuple[int, int]] = set()
    actions: dict[str, tuple[str, ...]] = {"A": ("move", "north")}

    resolve_movement([bot], actions, 10, terrain=terrain, collected_crystals=collected)

    assert bot.energy == 60
    assert (5, 4) in collected


def test_crystal_only_grants_once() -> None:
    """Second step onto same crystal gives no bonus."""
    terrain = _simple_terrain(10, {(5, 4): CRYSTAL})
    collected: set[tuple[int, int]] = {(5, 4)}  # already collected
    bot = _make_bot("A", x=5, y=5)
    bot.energy = 50
    actions: dict[str, tuple[str, ...]] = {"A": ("move", "north")}

    events = resolve_movement([bot], actions, 10, terrain=terrain, collected_crystals=collected)

    assert bot.energy == 50  # no bonus
    crystal_events = [e for e in events if e.get("type") == "crystal_pickup"]
    assert len(crystal_events) == 0


def test_crystal_pickup_event_generated() -> None:
    """crystal_pickup event has correct fields."""
    terrain = _simple_terrain(10, {(5, 4): CRYSTAL})
    bot = _make_bot("A", x=5, y=5)
    bot.energy = 50
    collected: set[tuple[int, int]] = set()
    actions: dict[str, tuple[str, ...]] = {"A": ("move", "north")}

    events = resolve_movement([bot], actions, 10, terrain=terrain, collected_crystals=collected)

    crystal_events = [e for e in events if e.get("type") == "crystal_pickup"]
    assert len(crystal_events) == 1
    evt = crystal_events[0]
    assert evt["emoji"] == "A"
    assert evt["x"] == 5
    assert evt["y"] == 4
    assert evt["energy"] == 10


# ── Cycle 5: Spawn positions avoid walls ───────────────────────────


def test_spawn_positions_avoid_walls() -> None:
    """Spawn positions should not land on wall tiles."""
    # Build a terrain where most of the grid is walls except a small area
    overrides: dict[tuple[int, int], str] = {}
    grid_size = 12
    for y in range(grid_size):
        for x in range(grid_size):
            # Only leave a 4x4 open area in center (4,4)-(7,7)
            if not (4 <= x <= 7 and 4 <= y <= 7):
                overrides[(x, y)] = WALL
    terrain = _simple_terrain(grid_size, overrides)

    rng = random.Random(42)
    positions = spawn_positions(4, grid_size, rng, terrain=terrain)

    assert len(positions) == 4
    for x, y in positions:
        assert terrain.is_walkable(x, y), f"Spawn at ({x},{y}) is on a wall!"


def test_spawn_positions_without_terrain() -> None:
    """spawn_positions still works when terrain is None (backward compat)."""
    rng = random.Random(42)
    positions = spawn_positions(4, 10, rng)
    assert len(positions) == 4
