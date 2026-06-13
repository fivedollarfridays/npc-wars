"""Build the state dict that each bot's decide() function receives."""

from typing import Any

from engine.combat import Bot
from engine.combat_rolls import calculate_hit_probability
from engine.equipment import EquipmentBonuses

__all__ = ["build_state"]


def _equip_kwargs(attacker: EquipmentBonuses, defender: EquipmentBonuses) -> dict[str, Any]:
    """Build equipment kwargs for calculate_hit_probability.

    Offensive terms come from the *attacker*'s loadout; defensive terms
    (DR, dodge) come from the *defender*'s loadout. Mirrors roll_attack.
    """
    return {
        "equipment_initiative": attacker.initiative,
        "equipment_to_hit": attacker.to_hit,
        "equipment_min_dmg": attacker.min_damage,
        "equipment_max_dmg": attacker.max_damage,
        "equipment_crit_mult": attacker.crit_mult,
        "equipment_crit_chance": attacker.crit_chance,
        "armor_pierce": attacker.armor_pierce,
        "equipment_dr": defender.dr,
        "equipment_dodge": defender.dodge,
    }


def _compute_incoming_threats(
    bot: Bot, alive_enemies: list[Bot],
) -> list[dict[str, object]]:
    """Compute incoming threat from each alive enemy, sorted by danger."""
    threats: list[tuple[float, dict[str, object]]] = []
    for enemy in alive_enemies:
        prob = calculate_hit_probability(
            enemy.derived, bot.derived,
            **_equip_kwargs(enemy.equipment_bonuses, bot.equipment_bonuses),
        )
        entry: dict[str, object] = {
            "emoji": enemy.emoji,
            "hit_chance": prob["hit_chance"],
            "expected_damage": prob["expected_damage"],
        }
        threats.append((prob["expected_damage"], entry))
    threats.sort(key=lambda t: t[0], reverse=True)
    return [t[1] for t in threats]


def build_state(
    bot: Bot, all_bots: list[Bot], round_num: int, grid_size: int,
    storm_border: int, bumps_last_round: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the state dict for a specific bot."""
    alive_enemies = [b for b in all_bots if b.alive and b.emoji != bot.emoji]

    hit_chance_vs: dict[str, dict[str, float]] = {}
    for enemy in alive_enemies:
        hit_chance_vs[enemy.emoji] = calculate_hit_probability(
            bot.derived, enemy.derived,
            **_equip_kwargs(bot.equipment_bonuses, enemy.equipment_bonuses),
        )

    # Incoming threats: how dangerous each enemy is TO this bot
    incoming_threat = _compute_incoming_threats(bot, alive_enemies)

    me_dict = bot.to_self_dict()
    me_dict["hit_chance_vs"] = hit_chance_vs
    me_dict["incoming_threat"] = incoming_threat

    return {
        "me": me_dict,
        "enemies": [e.to_enemy_dict() for e in alive_enemies],
        "round": round_num,
        "grid_size": grid_size,
        "storm_border": storm_border,
        "bumps_last_round": bumps_last_round or [],
    }
