"""Movement resolution helpers extracted from rounds.py.

Handles move/dash action validation, terrain effects (walls, crystals,
water), and bump collision resolution for the per-round movement phase.
"""

from __future__ import annotations

from typing import Any

from engine.combat import Bot
from engine.bumpers import resolve_bumps
from engine.grid import is_valid_position, apply_direction

__all__ = ["resolve_movement"]

_Action = tuple[str, ...]
_ActionsMap = dict[str, _Action]
_Event = dict[str, Any]

# Terrain constants (local copies to avoid importing engine.terrain at module level)
_CRYSTAL = "crystal"
_WATER = "water"
_CRYSTAL_ENERGY = 10
_WATER_EXTRA_COST = 5


def _collect_movers(
    alive_bots: list[Bot], actions: _ActionsMap, grid_size: int,
    terrain: Any | None,
) -> tuple[list[tuple[Bot, int, int]], list[_Event], list[_Event]]:
    """Iterate bots, validate move/dash actions, check terrain, build movers list."""
    movers: list[tuple[Bot, int, int]] = []
    dash_events: list[_Event] = []
    wall_events: list[_Event] = []
    for bot in alive_bots:
        action = actions.get(bot.emoji)
        if not action:
            continue
        if action[0] == "move":
            new_x, new_y = apply_direction(bot.x, bot.y, action[1])
            if not is_valid_position(new_x, new_y, grid_size):
                continue
            if terrain is not None and not terrain.is_walkable(new_x, new_y):
                wall_events.append({
                    "type": "wall_blocked", "emoji": bot.emoji,
                    "x": new_x, "y": new_y,
                })
                continue
            movers.append((bot, new_x, new_y))
        elif action[0] == "dash":
            mid_x, mid_y = apply_direction(bot.x, bot.y, action[1])
            if not is_valid_position(mid_x, mid_y, grid_size):
                continue  # Can't dash at all
            if terrain is not None and not terrain.is_walkable(mid_x, mid_y):
                wall_events.append({
                    "type": "wall_blocked", "emoji": bot.emoji,
                    "x": mid_x, "y": mid_y,
                })
                continue
            end_x, end_y = apply_direction(mid_x, mid_y, action[1])
            if is_valid_position(end_x, end_y, grid_size):
                if terrain is not None and not terrain.is_walkable(end_x, end_y):
                    dest_x, dest_y = mid_x, mid_y
                else:
                    dest_x, dest_y = end_x, end_y
            else:
                dest_x, dest_y = mid_x, mid_y
            movers.append((bot, dest_x, dest_y))
            dash_events.append({
                "type": "dash", "emoji": bot.emoji,
                "from_x": bot.x, "from_y": bot.y,
                "to_x": dest_x, "to_y": dest_y,
            })
    return movers, dash_events, wall_events


def _apply_terrain_effects(
    movers: list[tuple[Bot, int, int]], blocked: set[str],
    terrain: Any | None,
    collected_crystals: set[tuple[int, int]],
) -> tuple[list[_Event], list[_Event]]:
    """Apply position updates, handle crystal pickup and water penalties."""
    crystal_events: list[_Event] = []
    water_events: list[_Event] = []
    for bot, new_x, new_y in movers:
        if bot.emoji not in blocked:
            bot.x = new_x
            bot.y = new_y
            if terrain is not None:
                tile = terrain.get_tile(new_x, new_y)
                if tile == _CRYSTAL and (new_x, new_y) not in collected_crystals:
                    bot.energy = min(bot.energy + _CRYSTAL_ENERGY, bot.derived.max_energy)
                    collected_crystals.add((new_x, new_y))
                    crystal_events.append({
                        "type": "crystal_pickup", "emoji": bot.emoji,
                        "x": new_x, "y": new_y, "energy": _CRYSTAL_ENERGY,
                    })
                elif tile == _WATER:
                    bot.energy = max(0, bot.energy - _WATER_EXTRA_COST)
                    water_events.append({
                        "type": "water_penalty", "emoji": bot.emoji,
                        "x": new_x, "y": new_y, "cost": _WATER_EXTRA_COST,
                    })
    return crystal_events, water_events


def resolve_movement(
    alive_bots: list[Bot], actions: _ActionsMap, grid_size: int,
    all_bots: list[Bot] | None = None, storm_border: int = 0,
    terrain: Any | None = None,
    collected_crystals: set[tuple[int, int]] | None = None,
) -> list[_Event]:
    """Phase 3: Apply move/dash actions and resolve bump collisions.

    When *terrain* is provided, walls block movement, water costs extra
    energy, and crystal tiles grant a one-time energy bonus.
    """
    movers, dash_events, wall_events = _collect_movers(
        alive_bots, actions, grid_size, terrain,
    )
    bump_events, blocked = resolve_bumps(movers, all_bots or alive_bots, grid_size, storm_border)
    crystals = collected_crystals if collected_crystals is not None else set()
    crystal_events, water_events = _apply_terrain_effects(
        movers, blocked, terrain, crystals,
    )
    return wall_events + dash_events + bump_events + crystal_events + water_events
