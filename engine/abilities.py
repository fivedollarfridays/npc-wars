"""Ability system: bot-defined custom abilities via power_up callback."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from engine.combat import Bot

__all__ = [
    "ABILITY_TYPES",
    "AbilityDef",
    "validate_ability",
    "resolve_ability",
    "resolve_ability_phase",
    "tick_ability_cooldowns",
    "tick_ability_effects",
]

logger = logging.getLogger(__name__)

ABILITY_TYPES: frozenset[str] = frozenset({"damage", "heal", "shield", "slow"})


@dataclass(frozen=True)
class AbilityDef:
    """Immutable definition of a bot's custom ability."""

    name: str
    type: str
    potency: int
    range: int
    cooldown: int
    energy_cost: int


def validate_ability(definition: Any) -> AbilityDef | None:
    """Validate a power_up() return value. Returns AbilityDef or None."""
    if not isinstance(definition, dict):
        return None

    required = ("name", "type", "potency", "range", "cooldown", "energy_cost")
    for key in required:
        if key not in definition:
            return None

    name = definition["name"]
    if not isinstance(name, str) or not (1 <= len(name) <= 30):
        return None

    atype = definition["type"]
    if atype not in ABILITY_TYPES:
        return None

    potency = definition["potency"]
    if not isinstance(potency, int) or not (1 <= potency <= 50):
        return None

    arange = definition["range"]
    if not isinstance(arange, int) or not (0 <= arange <= 3):
        return None

    cooldown = definition["cooldown"]
    if not isinstance(cooldown, int) or not (2 <= cooldown <= 10):
        return None

    energy_cost = definition["energy_cost"]
    if not isinstance(energy_cost, int) or not (10 <= energy_cost <= 40):
        return None

    return AbilityDef(
        name=name, type=atype, potency=potency,
        range=arange, cooldown=cooldown, energy_cost=energy_cost,
    )


def resolve_ability(
    bot: Bot, target: Bot | None, ability: AbilityDef | None,
    round_num: int, all_bots: list[Bot],
) -> list[dict[str, Any]]:
    """Resolve an ability activation. Returns list of events."""
    if ability is None:
        return []
    bot.energy = max(0, bot.energy - ability.energy_cost)
    bot.ability_cooldown = ability.cooldown
    bot.ability_uses += 1

    if ability.type == "damage":
        return _resolve_damage(bot, target, ability)
    if ability.type == "heal":
        return _resolve_heal(bot, ability)
    if ability.type == "shield":
        return _resolve_shield(bot, ability)
    if ability.type == "slow":
        return _resolve_slow(bot, target, ability)
    return []


def _resolve_damage(
    bot: Bot, target: Bot | None, ability: AbilityDef,
) -> list[dict[str, Any]]:
    """Deal potency damage to target."""
    if target is None:
        return []
    hp_before = target.hp
    target.hp -= ability.potency
    target.damage_taken += ability.potency
    bot.damage_dealt += ability.potency
    return [{"type": "ability_damage", "emoji": bot.emoji,
             "target": target.emoji, "ability": ability.name,
             "damage": ability.potency, "hp_before": round(hp_before, 2)}]


def _resolve_heal(bot: Bot, ability: AbilityDef) -> list[dict[str, Any]]:
    """Restore potency HP to self, capped at max."""
    max_hp = float(bot.derived.max_hp)
    heal_amount = min(ability.potency, max_hp - bot.hp)
    heal_amount = max(0, heal_amount)
    bot.hp = min(max_hp, bot.hp + heal_amount)
    return [{"type": "ability_heal", "emoji": bot.emoji,
             "ability": ability.name, "healed": round(heal_amount, 2)}]


def _resolve_shield(bot: Bot, ability: AbilityDef) -> list[dict[str, Any]]:
    """Grant temp DR for 2 rounds."""
    bot.ability_shield = ability.potency
    bot.ability_shield_rounds = 2
    return [{"type": "ability_shield", "emoji": bot.emoji,
             "ability": ability.name, "dr": ability.potency, "rounds": 2}]


def _resolve_slow(
    bot: Bot, target: Bot | None, ability: AbilityDef,
) -> list[dict[str, Any]]:
    """Reduce target initiative for 3 rounds."""
    if target is None:
        return []
    target.ability_slow = ability.potency
    target.ability_slow_rounds = 3
    return [{"type": "ability_slow", "emoji": bot.emoji,
             "target": target.emoji, "ability": ability.name,
             "slow": ability.potency, "rounds": 3}]


def tick_ability_effects(bots: list[Bot]) -> None:
    """Decrement ability effect durations, clear expired effects."""
    for bot in bots:
        if bot.ability_shield_rounds > 0:
            bot.ability_shield_rounds -= 1
            if bot.ability_shield_rounds == 0:
                bot.ability_shield = 0
        if bot.ability_slow_rounds > 0:
            bot.ability_slow_rounds -= 1
            if bot.ability_slow_rounds == 0:
                bot.ability_slow = 0


def tick_ability_cooldowns(bots: list[Bot]) -> None:
    """Decrement ability cooldowns each round."""
    for bot in bots:
        if bot.ability_cooldown > 0:
            bot.ability_cooldown -= 1


def _find_ability_target(
    bot: Bot, direction: str | None, ability_range: int, all_bots: list[Bot],
) -> Bot | None:
    """Find target in direction within ability range."""
    if direction is None:
        return None
    from engine.grid import apply_direction
    cx, cy = bot.x, bot.y
    for _ in range(ability_range):
        cx, cy = apply_direction(cx, cy, direction)
        for b in all_bots:
            if b.alive and b.emoji != bot.emoji and b.x == cx and b.y == cy:
                return b
    return None


def resolve_ability_phase(
    alive_bots: list[Bot], all_bots: list[Bot],
    actions: dict[str, tuple[str, ...]], round_num: int,
) -> list[dict[str, Any]]:
    """Resolve use_ability actions for all alive bots."""
    events: list[dict[str, Any]] = []
    for bot in alive_bots:
        action = actions.get(bot.emoji)
        if not (action and action[0] == "use_ability"):
            continue
        if bot.ability is None:
            continue
        if bot.ability_cooldown > 0:
            continue
        if bot.energy < bot.ability.energy_cost:
            continue
        direction = action[1] if len(action) > 1 else None
        target = None
        if bot.ability.type in ("damage", "slow"):
            target = _find_ability_target(bot, direction, bot.ability.range, all_bots)
            if target is None:
                continue
        events.extend(resolve_ability(bot, target, bot.ability, round_num, all_bots))
    return events
