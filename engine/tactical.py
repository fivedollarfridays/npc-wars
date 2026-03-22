"""Tactical item activation and effect management."""

from __future__ import annotations

from typing import Any

from engine.combat import Bot
from engine.equipment import EQUIPMENT_CATALOG

__all__ = [
    "resolve_tactical_activation",
    "apply_overdrive",
    "tick_tactical_effects",
    "tick_tactical_cooldowns",
]

TACTICAL_CATALOG: dict[str, dict[str, Any]] = EQUIPMENT_CATALOG["tactical"]


def resolve_tactical_activation(
    bot: Bot, round_num: int, direction: str | None = None,
) -> list[dict[str, Any]]:
    """Attempt to activate a bot's tactical item. Returns events list."""
    tac_name = bot.equipment.get("tactical")
    if not tac_name or tac_name not in TACTICAL_CATALOG:
        return []

    item = TACTICAL_CATALOG[tac_name]
    if item["type"] != "activated":
        return []

    if bot.tactical_cooldown > 0:
        return []

    energy_cost: int = item["energy_cost"]
    if bot.energy < energy_cost:
        return []

    bot.energy -= energy_cost
    bot.tactical_cooldown = item["cooldown"]

    effect = _apply_tactical_effect(bot, tac_name, item, direction)

    return [{
        "type": "tactical_activate",
        "emoji": bot.emoji,
        "tactical": tac_name,
        "effect": effect,
    }]


def _apply_tactical_effect(
    bot: Bot, name: str, item: dict[str, Any], direction: str | None,
) -> str:
    """Apply the specific tactical effect. Returns description."""
    if name == "battle_cry":
        bot.tactical_damage_mult = item["damage_mult"]
        return "1.5x damage this round"

    if name == "fortify":
        bot.tactical_dr_bonus = item["dr_bonus_temp"]
        bot.tactical_temp_hp = item["hp_bonus_temp"]
        bot.hp += item["hp_bonus_temp"]
        return f"+{item['dr_bonus_temp']} DR, +{item['hp_bonus_temp']} temp HP"

    if name == "teleport":
        if direction is not None:
            from engine.grid import apply_direction
            for _ in range(item["distance"]):
                bot.x, bot.y = apply_direction(bot.x, bot.y, direction)
        return f"teleport {item['distance']} tiles {direction or 'nowhere'}"

    return "unknown"


def apply_overdrive(bot: Bot) -> None:
    """Apply overdrive passive bonuses at match start."""
    tac_name = bot.equipment.get("tactical")
    if tac_name != "overdrive":
        return
    item = TACTICAL_CATALOG["overdrive"]
    bot.equipment_bonuses.min_damage += item["damage_bonus"]
    bot.equipment_bonuses.max_damage += item["damage_bonus"]
    # Increase attack energy cost
    current = bot.equipment_bonuses.action_cost_mods.get("attack", 0)
    bot.equipment_bonuses.action_cost_mods["attack"] = current + item["attack_energy_increase"]


def tick_tactical_effects(bots: list[Bot]) -> None:
    """Clear expired tactical effects at end of round."""
    for bot in bots:
        bot.tactical_damage_mult = 1.0
        if bot.tactical_dr_bonus > 0:
            bot.tactical_dr_bonus = 0
        if bot.tactical_temp_hp > 0:
            bot.hp = max(1.0, bot.hp - bot.tactical_temp_hp)
            bot.tactical_temp_hp = 0


def tick_tactical_cooldowns(bots: list[Bot]) -> None:
    """Decrement tactical cooldowns each round."""
    for bot in bots:
        if bot.tactical_cooldown > 0:
            bot.tactical_cooldown -= 1
