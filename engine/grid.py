"""Grid, spawning, and storm logic for NPC Wars."""

import math
import random

__all__ = [
    "calculate_grid_size", "spawn_positions", "get_storm_border",
    "is_in_storm", "is_valid_position", "DIRECTIONS", "apply_direction",
    "direction_toward",
]


def calculate_grid_size(player_count: int) -> int:
    """Auto-calculate grid size from player count."""
    return max(10, int(math.sqrt(player_count) * 5))


def spawn_positions(player_count: int, grid_size: int, rng: random.Random) -> list[tuple[int, int]]:
    """Generate spawn positions with minimum 3-tile spacing, 2+ tiles from edge."""
    min_spacing = 3
    edge_buffer = 2
    positions: list[tuple[int, int]] = []

    attempts = 0
    max_attempts = 10000

    while len(positions) < player_count and attempts < max_attempts:
        x = rng.randint(edge_buffer, grid_size - 1 - edge_buffer)
        y = rng.randint(edge_buffer, grid_size - 1 - edge_buffer)
        attempts += 1

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
                positions.append((x, y))

    return positions


def get_storm_border(round_num: int) -> int:
    """Calculate storm border for a given round.

    Returns the number of tiles from edge that are in the storm.
    0 = no storm, 1 = outermost ring is storm, etc.
    """
    if round_num <= 9:
        return 0
    elif round_num <= 29:
        # Closing: moves in 1 tile per 5 rounds
        return (round_num - 9) // 5
    else:
        # Endgame: moves in 1 tile per 2 rounds, continuing from where closing left off
        closing_border = 4  # (29-9)//5 = 4 tiles in by end of closing
        return closing_border + (round_num - 29) // 2


def is_in_storm(x: int, y: int, grid_size: int, storm_border: int) -> bool:
    """Check if a position is inside the storm (outside safe zone).

    NOTE: duplicated in npcwars/_util.py for sandbox safety — keep in sync.
    """
    if storm_border <= 0:
        return False
    return (x < storm_border or x >= grid_size - storm_border or
            y < storm_border or y >= grid_size - storm_border)


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

    Ties broken by x-axis. Same position returns "north" (arbitrary).

    NOTE: duplicated in npcwars/_util.py for sandbox safety — keep in sync.
    """
    dx = to_x - from_x
    dy = to_y - from_y
    if dx == 0 and dy == 0:
        return "north"
    if abs(dx) >= abs(dy):
        return "east" if dx > 0 else "west"
    return "south" if dy > 0 else "north"
