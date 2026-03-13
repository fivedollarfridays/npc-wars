"""Per-round phase helpers for the match engine."""

from collections import defaultdict
from typing import Any

from engine.combat import (
    Bot, STORM_DAMAGE, REST_HEAL, REST_ENERGY_RESTORE, DEFEND_BONUS,
    MAX_HP, MAX_ENERGY, MAX_CONSECUTIVE_FAILURES, STARTING_DEFENSE,
    KILL_BOUNTY_ENERGY, calculate_damage,
)
from engine.bumpers import resolve_bumps
from engine.grid import is_in_storm, is_valid_position, apply_direction
from engine.state import build_state
from engine.sandbox import execute_decide, validate_action

__all__ = [
    "resolve_decisions", "resolve_defense", "resolve_movement",
    "resolve_attacks", "apply_storm_damage", "apply_energy_and_rest",
    "attribute_kills", "build_round_record",
]

_Action = tuple[str, ...]
_ActionsMap = dict[str, _Action]
_Event = dict[str, Any]


def resolve_decisions(
    alive_bots: list[Bot], bots: list[Bot], round_num: int,
    grid_size: int, storm_border: int,
    bumps_last_round: list[_Event] | None = None,
) -> tuple[_ActionsMap, set[str]]:
    """Phase 1: All bots decide their action. Returns (actions, forced_rest)."""
    actions: _ActionsMap = {}
    forced_rest: set[str] = set()
    for bot in alive_bots:
        if not bot.can_act():
            actions[bot.emoji] = ("rest",)
            forced_rest.add(bot.emoji)
            bot.consecutive_failures = 0
            continue

        state = build_state(bot, bots, round_num, grid_size, storm_border,
                            bumps_last_round=bumps_last_round)
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


def resolve_defense(alive_bots: list[Bot], actions: _ActionsMap) -> None:
    """Phase 2: Reset and apply defense bonuses."""
    for bot in alive_bots:
        bot.defense = STARTING_DEFENSE
        action = actions.get(bot.emoji)
        if action and action[0] == "defend":
            bot.defense = DEFEND_BONUS


def resolve_movement(
    alive_bots: list[Bot], actions: _ActionsMap, grid_size: int,
    all_bots: list[Bot] | None = None, storm_border: int = 0,
) -> list[_Event]:
    """Phase 3: Apply move actions and resolve bump collisions."""
    movers: list[tuple[Bot, int, int]] = []
    for bot in alive_bots:
        action = actions.get(bot.emoji)
        if action and action[0] == "move":
            new_x, new_y = apply_direction(bot.x, bot.y, action[1])
            if is_valid_position(new_x, new_y, grid_size):
                movers.append((bot, new_x, new_y))

    bump_events, blocked = resolve_bumps(movers, all_bots or alive_bots, grid_size, storm_border)

    for bot, new_x, new_y in movers:
        if bot.emoji not in blocked:
            bot.x = new_x
            bot.y = new_y

    return bump_events


def resolve_attacks(alive_bots: list[Bot], actions: _ActionsMap) -> list[_Event]:
    """Phase 4: Resolve attack actions and return hit/miss events."""
    pos_map: defaultdict[tuple[int, int], list[Bot]] = defaultdict(list)
    for b in alive_bots:
        pos_map[(b.x, b.y)].append(b)
    events: list[_Event] = []
    for bot in alive_bots:
        if not bot.alive:
            continue
        action = actions.get(bot.emoji)
        if not (action and action[0] == "attack"):
            continue
        target_x, target_y = apply_direction(bot.x, bot.y, action[1])
        targets_at_pos = pos_map.get((target_x, target_y), [])
        target: Bot | None = None
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


def apply_storm_damage(alive_bots: list[Bot], grid_size: int, storm_border: int) -> list[_Event]:
    """Phase 5: Apply storm damage and return storm events."""
    events: list[_Event] = []
    for bot in alive_bots:
        if bot.alive and is_in_storm(bot.x, bot.y, grid_size, storm_border):
            bot.hp -= STORM_DAMAGE
            bot.damage_taken += STORM_DAMAGE
            events.append({"type": "storm_damage", "target": bot.emoji, "damage": STORM_DAMAGE})
    return events


def apply_energy_and_rest(
    alive_bots: list[Bot], actions: _ActionsMap, forced_rest: set[str],
) -> None:
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


def attribute_kills(
    round_elims: list[_Event], round_events: list[_Event],
    bots: list[Bot], round_num: int,
) -> None:
    """Find killing blow and attribute kills to attackers."""
    for elim in round_elims:
        killer_emoji: str | None = None
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
                    b.energy = min(b.energy + KILL_BOUNTY_ENERGY, MAX_ENERGY)
        round_events.append({"type": "kill", "attacker": killer_emoji or "unknown",
                             "victim": elim["emoji"], "round": round_num})


def build_round_record(
    bots: list[Bot], actions: _ActionsMap, round_num: int,
    storm_border: int, events: list[_Event],
) -> _Event:
    """Build the round data dict for match output."""
    positions: list[_Event] = []
    for bot in bots:
        action_str = " ".join(str(a) for a in actions.get(bot.emoji, ("dead",)))
        positions.append({
            "emoji": bot.emoji, "x": bot.x, "y": bot.y,
            "hp": bot.hp, "energy": bot.energy,
            "action": action_str, "alive": bot.alive,
        })
    return {"round": round_num, "storm_border": storm_border,
            "positions": positions, "events": events}
