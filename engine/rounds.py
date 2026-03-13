"""Per-round phase helpers for the match engine."""

from collections import defaultdict

from engine.combat import (
    STORM_DAMAGE, REST_HEAL, REST_ENERGY_RESTORE, DEFEND_BONUS,
    MAX_HP, MAX_ENERGY, MAX_CONSECUTIVE_FAILURES, STARTING_DEFENSE,
    calculate_damage,
)
from engine.grid import is_in_storm, is_valid_position, apply_direction
from engine.state import build_state
from engine.sandbox import execute_decide, validate_action

__all__ = [
    "resolve_decisions", "resolve_defense", "resolve_movement",
    "resolve_attacks", "apply_storm_damage", "apply_energy_and_rest",
    "attribute_kills", "build_round_record",
]


def resolve_decisions(alive_bots, bots, round_num, grid_size, storm_border):
    """Phase 1: All bots decide their action. Returns (actions, forced_rest)."""
    actions = {}
    forced_rest = set()
    for bot in alive_bots:
        if not bot.can_act():
            actions[bot.emoji] = ("rest",)
            forced_rest.add(bot.emoji)
            bot.consecutive_failures = 0
            continue

        state = build_state(bot, bots, round_num, grid_size, storm_border)
        raw_action = execute_decide(bot.decide_func, state)
        action = validate_action(raw_action)

        if action is None:
            bot.consecutive_failures += 1
            if bot.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                bot.hp = 0
                actions[bot.emoji] = ("disconnected",)
            else:
                actions[bot.emoji] = ("nothing",)
        else:
            bot.consecutive_failures = 0
            actions[bot.emoji] = action
    return actions, forced_rest


def resolve_defense(alive_bots, actions):
    """Phase 2: Reset and apply defense bonuses."""
    for bot in alive_bots:
        bot.defense = STARTING_DEFENSE
        action = actions.get(bot.emoji)
        if action and action[0] == "defend":
            bot.defense = DEFEND_BONUS


def resolve_movement(alive_bots, actions, grid_size):
    """Phase 3: Apply move actions."""
    for bot in alive_bots:
        action = actions.get(bot.emoji)
        if action and action[0] == "move":
            new_x, new_y = apply_direction(bot.x, bot.y, action[1])
            if is_valid_position(new_x, new_y, grid_size):
                bot.x = new_x
                bot.y = new_y


def resolve_attacks(alive_bots, actions):
    """Phase 4: Resolve attack actions and return hit/miss events."""
    pos_map = defaultdict(list)
    for b in alive_bots:
        pos_map[(b.x, b.y)].append(b)
    events = []
    for bot in alive_bots:
        if not bot.alive:
            continue
        action = actions.get(bot.emoji)
        if not (action and action[0] == "attack"):
            continue
        target_x, target_y = apply_direction(bot.x, bot.y, action[1])
        targets_at_pos = pos_map.get((target_x, target_y), [])
        target = None
        for t in targets_at_pos:
            if t.emoji != bot.emoji and t.alive:
                target = t
                break
        if target:
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


def apply_storm_damage(alive_bots, grid_size, storm_border):
    """Phase 5: Apply storm damage and return storm events."""
    events = []
    for bot in alive_bots:
        if bot.alive and is_in_storm(bot.x, bot.y, grid_size, storm_border):
            bot.hp -= STORM_DAMAGE
            bot.damage_taken += STORM_DAMAGE
            events.append({"type": "storm_damage", "target": bot.emoji, "damage": STORM_DAMAGE})
    return events


def apply_energy_and_rest(alive_bots, actions, forced_rest):
    """Phase 6+7: Deduct energy costs and apply explicit rest healing."""
    for bot in alive_bots:
        action = actions.get(bot.emoji)
        if action and action[0] not in ("nothing", "disconnected") and bot.emoji not in forced_rest:
            bot.apply_action_cost(action[0])
    for bot in alive_bots:
        action = actions.get(bot.emoji)
        if action and action[0] == "rest":
            bot.hp = min(MAX_HP, bot.hp + REST_HEAL)
            bot.energy = min(MAX_ENERGY, bot.energy + REST_ENERGY_RESTORE)


def attribute_kills(round_elims, round_events, bots, round_num):
    """Find killing blow and attribute kills to attackers."""
    for elim in round_elims:
        killer_emoji = None
        for evt in round_events:
            if (evt.get("type") == "hit" and evt.get("target") == elim["emoji"]
                    and evt.get("hp_before", 1) > 0
                    and evt["hp_before"] - evt["damage"] <= 0):
                killer_emoji = evt["attacker"]
                break
        if killer_emoji is None:
            for evt in round_events:
                if evt.get("type") == "hit" and evt.get("target") == elim["emoji"]:
                    killer_emoji = evt["attacker"]
        if killer_emoji is None:
            for evt in round_events:
                if evt.get("type") == "storm_damage" and evt.get("target") == elim["emoji"]:
                    killer_emoji = "storm"
        elim["killed_by"] = killer_emoji or "unknown"
        elim["cause"] = "storm" if killer_emoji == "storm" else "combat"
        if killer_emoji and killer_emoji != "storm":
            for b in bots:
                if b.emoji == killer_emoji:
                    b.kills += 1
        round_events.append({"type": "kill", "attacker": killer_emoji or "unknown",
                             "victim": elim["emoji"], "round": round_num})


def build_round_record(bots, actions, round_num, storm_border, events):
    """Build the round data dict for match output."""
    positions = []
    for bot in bots:
        action_str = " ".join(str(a) for a in actions.get(bot.emoji, ("dead",)))
        positions.append({
            "emoji": bot.emoji, "x": bot.x, "y": bot.y,
            "hp": bot.hp, "energy": bot.energy,
            "action": action_str, "alive": bot.alive,
        })
    return {"round": round_num, "storm_border": storm_border,
            "positions": positions, "events": events}
