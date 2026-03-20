"""Passivity plague — progressive penalty for bots that avoid combat.

Bots earn a grace period to position, but sustained passivity triggers
escalating energy drain and HP damage. Engaging in combat resets the counter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from engine.combat import Bot

__all__ = [
    "PLAGUE_GRACE_ROUNDS",
    "PLAGUE_ENERGY_DRAIN",
    "PLAGUE_HP_BASE",
    "PLAGUE_HP_ESCALATION",
    "ENGAGE_RANGE",
    "is_active_action",
    "update_passivity",
    "apply_plague",
]

# Grace period before plague kicks in
PLAGUE_GRACE_ROUNDS: int = 3

# Per-round penalties (applied after grace)
PLAGUE_ENERGY_DRAIN: int = 12
PLAGUE_HP_BASE: int = 5
PLAGUE_HP_ESCALATION: int = 3  # +3 HP damage per round past grace

# Range within which defend counts as active
ENGAGE_RANGE: int = 3


def is_active_action(
    action: tuple[str, ...], bot: Bot, enemies: list[dict[str, Any]],
) -> bool:
    """Return True if the action counts as combat engagement.

    Active actions: attack, ranged_attack, taunt, defend near enemies,
    move toward closest enemy.
    """
    if not action:
        return False

    act = action[0]

    # Attacks and taunts are always active
    if act in ("attack", "ranged_attack", "taunt", "dash"):
        return True

    # Defend is active only if enemies are within engage range
    if act == "defend":
        return _any_enemy_within(bot, enemies, ENGAGE_RANGE)

    # Move toward closest enemy is active
    if act == "move" and len(action) > 1:
        return _move_closes_distance(bot, enemies, action[1])

    return False


def _any_enemy_within(
    bot: Bot, enemies: list[dict[str, Any]], max_dist: int,
) -> bool:
    """Check if any enemy is within max_dist Manhattan distance."""
    for e in enemies:
        d = abs(e["x"] - bot.x) + abs(e["y"] - bot.y)
        if d <= max_dist:
            return True
    return False


def _move_closes_distance(
    bot: Bot, enemies: list[dict[str, Any]], direction: str,
) -> bool:
    """Check if moving in this direction reduces distance to closest enemy."""
    if not enemies:
        return False

    closest = min(enemies, key=lambda e: abs(int(e["x"]) - bot.x) + abs(int(e["y"]) - bot.y))
    cx, cy = int(closest["x"]), int(closest["y"])
    current_dist = abs(cx - bot.x) + abs(cy - bot.y)

    _DIRS: dict[str, tuple[int, int]] = {
        "north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0),
    }
    dx, dy = _DIRS.get(direction, (0, 0))
    new_dist = abs(cx - (bot.x + dx)) + abs(cy - (bot.y + dy))
    return bool(new_dist < current_dist)


def update_passivity(bot: Bot, *, is_active: bool) -> None:
    """Update the bot's passive round counter."""
    if is_active:
        bot.passive_rounds = 0
    else:
        bot.passive_rounds += 1


def apply_plague(bot: Bot) -> list[dict[str, Any]]:
    """Apply progressive plague penalties. Returns plague events."""
    if not bot.alive or bot.hp <= 0:
        return []

    if bot.passive_rounds < PLAGUE_GRACE_ROUNDS:
        return []

    rounds_past_grace = bot.passive_rounds - PLAGUE_GRACE_ROUNDS
    events: list[dict[str, Any]] = []

    # Energy drain (constant)
    energy_lost = min(bot.energy, PLAGUE_ENERGY_DRAIN)
    bot.energy = max(0, bot.energy - PLAGUE_ENERGY_DRAIN)

    # HP damage (escalating)
    hp_damage = PLAGUE_HP_BASE + rounds_past_grace * PLAGUE_HP_ESCALATION
    bot.hp = max(1, bot.hp - hp_damage)  # never kills, leaves at 1 HP

    events.append({
        "type": "plague",
        "emoji": bot.emoji,
        "hp_damage": hp_damage,
        "energy_drain": energy_lost,
        "passive_rounds": bot.passive_rounds,
    })

    return events
