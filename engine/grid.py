"""Grid, spawning, and storm logic for NPC Wars."""

import math
import random
from typing import Any

__all__ = [
    "calculate_grid_size", "spawn_positions", "get_storm_border",
    "is_in_storm", "is_valid_position", "DIRECTIONS", "apply_direction",
    "direction_toward",
]


def calculate_grid_size(player_count: int) -> int:
    """Auto-calculate grid size from player count."""
    return max(10, int(math.sqrt(player_count) * 5))


def spawn_positions(
    player_count: int, grid_size: int, rng: random.Random,
    terrain: Any | None = None,
) -> list[tuple[int, int]]:
    """Generate spawn positions with minimum 3-tile spacing, 2+ tiles from edge.

    When *terrain* is provided, positions on non-walkable tiles are rejected.
    """
    min_spacing = 3
    edge_buffer = 2
    positions: list[tuple[int, int]] = []

    attempts = 0
    max_attempts = 10000

    while len(positions) < player_count and attempts < max_attempts:
        x = rng.randint(edge_buffer, grid_size - 1 - edge_buffer)
        y = rng.randint(edge_buffer, grid_size - 1 - edge_buffer)
        attempts += 1

        # Reject non-walkable tiles
        if terrain is not None and not terrain.is_walkable(x, y):
            continue

        # Check minimum spacing from all existing positions
        too_close = False
        for px, py in positions:
            if abs(x - px) + abs(y - py) < min_spacing:
                too_close = True
                break

        if not too_close:
            positions.append((x, y))

    if len(positions) < player_count:
        # Fallback: relax spacing constraints
        while len(positions) < player_count:
            x = rng.randint(edge_buffer, grid_size - 1 - edge_buffer)
            y = rng.randint(edge_buffer, grid_size - 1 - edge_buffer)
            if (x, y) not in positions:
                if terrain is None or terrain.is_walkable(x, y):
                    positions.append((x, y))

    return positions


def get_storm_border(round_num: int, grid_size: int | None = None) -> int:
    """Calculate storm border for a given round.

    Returns the number of tiles from edge that are in the storm.
    0 = no storm, 1 = outermost ring is storm, etc.

    When *grid_size* is provided, the border is clamped so the safe zone
    (side length ``grid_size - 2*border``) never shrinks below a 2x2 box,
    i.e. ``border <= (grid_size - 2) // 2``. Without *grid_size* the raw
    (unclamped) schedule is returned for backward compatibility.
    """
    if round_num <= 9:
        border = 0
    elif round_num <= 29:
        # Closing: moves in 1 tile per 5 rounds
        border = (round_num - 9) // 5
    else:
        # Endgame: moves in 1 tile per 2 rounds, continuing from where closing left off
        closing_border = 4  # (29-9)//5 = 4 tiles in by end of closing
        border = closing_border + (round_num - 29) // 2
    if grid_size is not None:
        max_border = max(0, (grid_size - 2) // 2)
        border = min(border, max_border)
    return border


def is_in_storm(x: int, y: int, grid_size: int, storm_border: int) -> bool:
    """Check if a position is inside the storm (outside safe zone)."""
    if storm_border <= 0:
        return False
    return (x < storm_border or x >= grid_size - storm_border or
            y < storm_border or y >= grid_size - storm_border)


def storm_depth(x: int, y: int, grid_size: int, storm_border: int) -> int:
    """How many tiles deep into the storm a position is (0 if safe)."""
    if storm_border <= 0:
        return 0
    depths = []
    if x < storm_border:
        depths.append(storm_border - x)
    if x >= grid_size - storm_border:
        depths.append(x - (grid_size - storm_border) + 1)
    if y < storm_border:
        depths.append(storm_border - y)
    if y >= grid_size - storm_border:
        depths.append(y - (grid_size - storm_border) + 1)
    return max(depths) if depths else 0


def is_valid_position(x: int, y: int, grid_size: int) -> bool:
    """Check if a position is within the grid bounds."""
    return 0 <= x < grid_size and 0 <= y < grid_size


DIRECTIONS = {
    "north": (0, -1),
    "south": (0, 1),
    "east": (1, 0),
    "west": (-1, 0),
}


def apply_direction(x: int, y: int, direction: str) -> tuple[int, int]:
    """Apply a movement direction to a position."""
    dx, dy = DIRECTIONS[direction]
    return x + dx, y + dy


def direction_toward(from_x: int, from_y: int, to_x: int, to_y: int) -> str:
    """Compute cardinal direction from one position toward another.

    Ties broken by x-axis. Same position returns "west" (arbitrary).
    """
    dx = to_x - from_x
    dy = to_y - from_y
    if abs(dx) >= abs(dy):
        return "east" if dx > 0 else "west"
    return "south" if dy > 0 else "north"
