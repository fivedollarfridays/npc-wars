"""Combat resolution helpers extracted from rounds.py.

Contains melee and ranged attack phases plus spatial lookup helpers.
"""

import random
from collections import defaultdict
from typing import Any

from engine.combat import Bot, RANGED_ATTACK_DAMAGE, calculate_damage
from engine.combat_rolls import (
    REST_HIT_BONUS,
    TAUNT_HIT_PENALTY,
    roll_attack,
    roll_ranged_attack,
)
from engine.grid import apply_direction

__all__ = ["resolve_attacks", "resolve_ranged_attacks", "build_pos_map"]

_Action = tuple[str, ...]
_ActionsMap = dict[str, _Action]
_Event = dict[str, Any]


def build_pos_map(alive_bots: list[Bot]) -> defaultdict[tuple[int, int], list[Bot]]:
    """Build position -> bot list map for O(1) spatial lookups."""
    pos_map: defaultdict[tuple[int, int], list[Bot]] = defaultdict(list)
    for b in alive_bots:
        pos_map[(b.x, b.y)].append(b)
    return pos_map


def _find_target(
    pos_map: defaultdict[tuple[int, int], list[Bot]],
    x: int, y: int, exclude_emoji: str,
) -> Bot | None:
    """Find first alive bot at (x, y) excluding the attacker."""
    for t in pos_map.get((x, y), []):
        if t.emoji != exclude_emoji and t.alive:
            return t
    return None


def resolve_attacks(alive_bots: list[Bot], actions: _ActionsMap,
                    pos_map: defaultdict[tuple[int, int], list[Bot]] | None = None,
                    rng: random.Random | None = None) -> list[_Event]:
    """Phase 4: Resolve attack actions and return hit/miss events."""
    if pos_map is None:
        pos_map = build_pos_map(alive_bots)
    events: list[_Event] = []
    # Initiative: higher SPEED resolves first (stable sort preserves ties)
    sorted_bots = sorted(alive_bots, key=lambda b: b.derived.initiative - b.ability_slow, reverse=True)
    for bot in sorted_bots:
        if not bot.alive or bot.hp <= 0:
            continue
        action = actions.get(bot.emoji)
        if not (action and action[0] == "attack"):
            continue
        target_x, target_y = apply_direction(bot.x, bot.y, action[1])
        target = _find_target(pos_map, target_x, target_y, bot.emoji)
        # Reach weapon: check further tiles if no adjacent target
        if target is None and bot.equipment_bonuses.reach_distance >= 2:
            rx, ry = target_x, target_y
            for _ in range(1, bot.equipment_bonuses.reach_distance):
                rx, ry = apply_direction(rx, ry, action[1])
                target = _find_target(pos_map, rx, ry, bot.emoji)
                if target:
                    break
        if target:
            if rng is not None:
                events.append(_roll_melee(bot, target, actions, rng))
            else:
                dmg = calculate_damage(bot, target)
                hp_before = target.hp
                target.hp -= dmg
                target.damage_taken += dmg
                bot.damage_dealt += dmg
                if dmg > 0:
                    events.append({"type": "hit", "attacker": bot.emoji,
                                   "target": target.emoji, "damage": dmg,
                                   "hp_before": hp_before})
        else:
            events.append({"type": "miss", "attacker": bot.emoji, "direction": action[1]})
    return events


def _compute_to_hit_mod(
    bot: Bot, target: Bot, actions: _ActionsMap,
) -> int:
    """Compute situational to-hit modifier for an attack."""
    to_hit_mod = 0
    target_action = actions.get(target.emoji)
    if target_action is not None and target_action[0] == "rest":
        to_hit_mod += REST_HIT_BONUS
    if bot.taunt_target is not None and target.emoji != bot.taunt_target:
        to_hit_mod -= TAUNT_HIT_PENALTY
    return to_hit_mod


def _roll_melee(bot: Bot, target: Bot, actions: _ActionsMap,
                rng: random.Random) -> _Event:
    """Resolve a melee attack using roll_attack and apply damage."""
    target_action = actions.get(target.emoji)
    defending = target_action is not None and target_action[0] == "defend"
    to_hit_mod = _compute_to_hit_mod(bot, target, actions)
    atk_eq = bot.equipment_bonuses
    def_eq = target.equipment_bonuses
    # Finesse weapon: speed-based to-hit bonus
    eq_to_hit = atk_eq.to_hit
    if atk_eq.special_weapon == "finesse":
        eq_to_hit += max(0, (bot.stats.speed - 25) // 10)
    result = roll_attack(
        bot.derived, target.derived, defending=defending, rng=rng,
        momentum_damage_mult=bot.momentum_damage_multiplier * bot.tactical_damage_mult,
        momentum_defense_reduct=target.momentum_defense_reduction,
        to_hit_modifier=to_hit_mod,
        equipment_to_hit=eq_to_hit,
        equipment_min_dmg=atk_eq.min_damage,
        equipment_max_dmg=atk_eq.max_damage,
        equipment_crit_mult=atk_eq.crit_mult,
        equipment_dr=def_eq.dr,
        armor_pierce=atk_eq.armor_pierce,
        tactical_dr=target.tactical_dr_bonus + target.ability_shield,
    )
    if result.hit:
        hp_before = target.hp
        target.hp -= result.damage
        target.damage_taken += int(result.damage)
        bot.damage_dealt += int(result.damage)
        return {"type": "hit", "attacker": bot.emoji, "target": target.emoji,
                "damage": result.damage, "hp_before": round(hp_before, 2),
                "roll": result.roll, "modifier": result.modifier,
                "ac": result.target_ac, "is_crit": result.is_crit,
                "dodged": result.dodged}
    return {"type": "attack_miss", "attacker": bot.emoji, "target": target.emoji,
            "roll": result.roll, "modifier": result.modifier, "ac": result.target_ac}


def resolve_ranged_attacks(alive_bots: list[Bot], actions: _ActionsMap,
                           pos_map: defaultdict[tuple[int, int], list[Bot]] | None = None,
                           rng: random.Random | None = None) -> list[_Event]:
    """Phase 4b: Resolve ranged attack actions (range 2)."""
    if pos_map is None:
        pos_map = build_pos_map(alive_bots)
    events: list[_Event] = []
    # Initiative: higher SPEED resolves first (stable sort preserves ties)
    sorted_bots = sorted(alive_bots, key=lambda b: b.derived.initiative - b.ability_slow, reverse=True)
    for bot in sorted_bots:
        if not bot.alive or bot.hp <= 0:
            continue
        action = actions.get(bot.emoji)
        if not (action and action[0] == "ranged_attack"):
            continue
        mid_x, mid_y = apply_direction(bot.x, bot.y, action[1])
        target_x, target_y = apply_direction(mid_x, mid_y, action[1])
        target = _find_target(pos_map, target_x, target_y, bot.emoji)
        if target:
            if rng is not None:
                events.append(_roll_ranged(bot, target, actions, rng))
            else:
                dmg = RANGED_ATTACK_DAMAGE
                hp_before = target.hp
                target.hp -= dmg
                target.damage_taken += dmg
                bot.damage_dealt += dmg
                events.append({"type": "ranged_hit", "attacker": bot.emoji,
                               "target": target.emoji, "damage": dmg,
                               "hp_before": hp_before})
        else:
            events.append({"type": "ranged_miss", "attacker": bot.emoji,
                           "direction": action[1]})
    return events


def _roll_ranged(bot: Bot, target: Bot, actions: _ActionsMap,
                 rng: random.Random) -> _Event:
    """Resolve a ranged attack using roll_ranged_attack and apply damage."""
    target_action = actions.get(target.emoji)
    defending = target_action is not None and target_action[0] == "defend"
    to_hit_mod = _compute_to_hit_mod(bot, target, actions)
    atk_eq = bot.equipment_bonuses
    def_eq = target.equipment_bonuses
    # Bow (ranged_preferred): add weapon to_hit as ranged bonus
    eq_to_hit = atk_eq.to_hit
    if atk_eq.special_weapon == "finesse":
        eq_to_hit += max(0, (bot.stats.speed - 25) // 10)
    result = roll_ranged_attack(
        bot.derived, target.derived, defending=defending, rng=rng,
        momentum_damage_mult=bot.momentum_damage_multiplier * bot.tactical_damage_mult,
        momentum_defense_reduct=target.momentum_defense_reduction,
        to_hit_modifier=to_hit_mod,
        equipment_to_hit=eq_to_hit,
        equipment_min_dmg=atk_eq.min_damage,
        equipment_max_dmg=atk_eq.max_damage,
        equipment_crit_mult=atk_eq.crit_mult,
        equipment_dr=def_eq.dr,
        armor_pierce=atk_eq.armor_pierce,
        tactical_dr=target.tactical_dr_bonus + target.ability_shield,
    )
    if result.hit:
        hp_before = target.hp
        target.hp -= result.damage
        target.damage_taken += int(result.damage)
        bot.damage_dealt += int(result.damage)
        return {"type": "ranged_hit", "attacker": bot.emoji, "target": target.emoji,
                "damage": result.damage, "hp_before": round(hp_before, 2),
                "roll": result.roll, "modifier": result.modifier,
                "ac": result.target_ac, "is_crit": result.is_crit,
                "dodged": result.dodged}
    return {"type": "ranged_attack_miss", "attacker": bot.emoji, "target": target.emoji,
            "roll": result.roll, "modifier": result.modifier, "ac": result.target_ac}
