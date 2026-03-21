"""Trap resolution helpers — placement, triggering, and cleanup for the match loop."""

from __future__ import annotations

from typing import Any

from engine.combat import Bot
from engine.grid import DIRECTIONS
from engine.traps import TrapManager

__all__ = [
    "resolve_trap_placement",
    "resolve_trap_triggers",
]

_Event = dict[str, Any]


def resolve_trap_placement(
    alive_bots: list[Bot],
    actions: dict[str, tuple[str, ...]],
    trap_manager: TrapManager,
    round_num: int,
    grid_size: int,
) -> list[_Event]:
    """Process trap placement actions. Returns placement events."""
    events: list[_Event] = []
    for bot in alive_bots:
        action = actions.get(bot.emoji)
        if not (action and action[0] == "trap"):
            continue
        direction = action[1]
        dx, dy = DIRECTIONS[direction]
        target_x = max(0, min(grid_size - 1, bot.x + dx))
        target_y = max(0, min(grid_size - 1, bot.y + dy))

        trap = trap_manager.place_trap(
            bot.emoji, target_x, target_y, bot.stats.power, round_num,
        )
        if trap is not None:
            events.append({
                "type": "trap_placed",
                "emoji": bot.emoji,
                "x": trap.x,
                "y": trap.y,
            })
    return events


def resolve_trap_triggers(
    alive_bots: list[Bot],
    trap_manager: TrapManager,
    round_num: int,
) -> list[_Event]:
    """Check all alive bots for trap triggers. Apply damage and return events."""
    events: list[_Event] = []
    owner_map = {b.emoji: b for b in alive_bots}
    for bot in alive_bots:
        if not bot.alive:
            continue
        triggered = trap_manager.check_triggers(bot.emoji, bot.x, bot.y, round_num)
        for trap in triggered:
            # Apply armor damage reduction (flat subtraction)
            raw_damage = trap.damage
            dr = bot.derived.damage_reduction
            actual_damage = max(1.0, raw_damage - dr)
            hp_before = bot.hp

            bot.hp -= actual_damage
            bot.damage_taken += int(actual_damage)

            # Credit trap owner with damage dealt
            owner = owner_map.get(trap.owner_emoji)
            if owner is not None:
                owner.damage_dealt += int(actual_damage)

            events.append({
                "type": "trap_trigger",
                "victim": bot.emoji,
                "owner": trap.owner_emoji,
                "damage": actual_damage,
                "hp_before": hp_before,
                "x": trap.x,
                "y": trap.y,
            })
    return events
