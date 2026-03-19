"""Per-round phase helpers for the match engine."""

from typing import Any

from engine.combat import (
    Bot, STORM_DAMAGE, REST_HEAL, REST_ENERGY_RESTORE, DEFEND_BONUS,
    MAX_CONSECUTIVE_FAILURES, STARTING_DEFENSE,
    KILL_BOUNTY_ENERGY, TAUNT_RANGE,
)
from engine.bumpers import resolve_bumps
from engine.grid import is_in_storm, is_valid_position, apply_direction, direction_toward
from engine.state import build_state
from engine.sandbox import execute_decide, validate_action
from engine.rounds_combat import (  # noqa: F401 — re-exported for backward compat
    resolve_attacks, resolve_ranged_attacks, build_pos_map,
)

__all__ = [
    "resolve_decisions", "resolve_defense", "resolve_movement",
    "resolve_attacks", "resolve_ranged_attacks", "resolve_taunt",
    "apply_storm_damage", "apply_energy_and_rest",
    "attribute_kills", "build_round_record", "build_pos_map",
]

_Action = tuple[str, ...]
_ActionsMap = dict[str, _Action]
_Event = dict[str, Any]


_HIT_TYPES = frozenset({"hit", "ranged_hit"})


def _apply_human_override(
    bot: Bot, state: dict[str, Any], action: _Action | None,
    override_events: list[_Event],
) -> _Action | None:
    """Try copilot override; append event if human picks a different action."""
    if bot.human_adapter is None:
        return action
    human_raw = bot.human_adapter.get_action(state, timeout_s=2.0)
    if human_raw is None:
        return action
    human_action = validate_action(
        human_raw, unlocked_actions=set(bot.unlocked_actions),
    )
    if human_action is not None and human_action != action:
        override_events.append({
            "type": "human_override",
            "player": bot.emoji,
            "original": " ".join(action) if action else "nothing",
            "override": " ".join(human_action),
        })
        return human_action
    return action


def resolve_decisions(
    alive_bots: list[Bot], bots: list[Bot], round_num: int,
    grid_size: int, storm_border: int,
    bumps_last_round: list[_Event] | None = None,
) -> tuple[_ActionsMap, set[str], list[_Event]]:
    """Phase 1: All bots decide their action. Returns (actions, forced_rest, override_events)."""
    actions: _ActionsMap = {}
    forced_rest: set[str] = set()
    override_events: list[_Event] = []
    for bot in alive_bots:
        if not bot.can_act():
            actions[bot.emoji] = ("rest",)
            forced_rest.add(bot.emoji)
            bot.consecutive_failures = 0
            continue

        state = build_state(bot, bots, round_num, grid_size, storm_border,
                            bumps_last_round=bumps_last_round)
        raw_action = execute_decide(bot.decide_func, state)
        action = validate_action(raw_action, unlocked_actions=set(bot.unlocked_actions))
        action = _apply_human_override(bot, state, action, override_events)

        if action is None:
            bot.consecutive_failures += 1
            if bot.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                bot.hp = 0
                actions[bot.emoji] = ("disconnected",)
            else:
                actions[bot.emoji] = ("nothing",)
        else:
            bot.consecutive_failures = 0
            # Taunt override: redirect attack/ranged_attack toward taunter
            if (bot.taunt_target is not None and action[0] in ("attack", "ranged_attack")):
                action = _apply_taunt_override(bot, action, bots)
            actions[bot.emoji] = action
    return actions, forced_rest, override_events


def _apply_taunt_override(
    bot: Bot, action: _Action, all_bots: list[Bot],
) -> _Action:
    """Redirect a taunted bot's attack toward the taunter, then clear taunt."""
    for b in all_bots:
        if b.emoji == bot.taunt_target and b.alive:
            d = direction_toward(bot.x, bot.y, b.x, b.y)
            bot.taunt_target = None
            return (action[0], d)
    # Taunter dead or missing -- clear and keep original action
    bot.taunt_target = None
    return action


def resolve_defense(alive_bots: list[Bot], actions: _ActionsMap) -> list[_Event]:
    """Phase 2: Reset and apply defense bonuses; emit defend events."""
    events: list[_Event] = []
    for bot in alive_bots:
        bot.defense = STARTING_DEFENSE
        action = actions.get(bot.emoji)
        if action and action[0] == "defend":
            bot.defense = DEFEND_BONUS
            events.append({"type": "defend", "emoji": bot.emoji})
    return events


def resolve_movement(
    alive_bots: list[Bot], actions: _ActionsMap, grid_size: int,
    all_bots: list[Bot] | None = None, storm_border: int = 0,
) -> list[_Event]:
    """Phase 3: Apply move/dash actions and resolve bump collisions."""
    movers: list[tuple[Bot, int, int]] = []
    dash_events: list[_Event] = []
    for bot in alive_bots:
        action = actions.get(bot.emoji)
        if not action:
            continue
        if action[0] == "move":
            new_x, new_y = apply_direction(bot.x, bot.y, action[1])
            if is_valid_position(new_x, new_y, grid_size):
                movers.append((bot, new_x, new_y))
        elif action[0] == "dash":
            mid_x, mid_y = apply_direction(bot.x, bot.y, action[1])
            if not is_valid_position(mid_x, mid_y, grid_size):
                continue  # Can't dash at all
            end_x, end_y = apply_direction(mid_x, mid_y, action[1])
            if is_valid_position(end_x, end_y, grid_size):
                dest_x, dest_y = end_x, end_y
            else:
                dest_x, dest_y = mid_x, mid_y
            movers.append((bot, dest_x, dest_y))
            dash_events.append({
                "type": "dash", "emoji": bot.emoji,
                "from_x": bot.x, "from_y": bot.y,
                "to_x": dest_x, "to_y": dest_y,
            })

    bump_events, blocked = resolve_bumps(movers, all_bots or alive_bots, grid_size, storm_border)

    for bot, new_x, new_y in movers:
        if bot.emoji not in blocked:
            bot.x = new_x
            bot.y = new_y

    return dash_events + bump_events


def resolve_taunt(alive_bots: list[Bot], actions: _ActionsMap) -> list[_Event]:
    """Process taunt actions: set taunt_target on nearby bots for next round."""
    events: list[_Event] = []
    for bot in alive_bots:
        action = actions.get(bot.emoji)
        if not (action and action[0] == "taunt"):
            continue
        affected: list[str] = []
        for other in alive_bots:
            if other.emoji == bot.emoji:
                continue
            dist = abs(other.x - bot.x) + abs(other.y - bot.y)
            if dist <= TAUNT_RANGE:
                other.taunt_target = bot.emoji
                affected.append(other.emoji)
        if affected:
            events.append({"type": "taunt", "taunter": bot.emoji, "affected": affected})
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
            bot.hp = min(bot.derived.max_hp, bot.hp + REST_HEAL)
            energy_restore = REST_ENERGY_RESTORE + bot.derived.energy_regen + bot.momentum_energy_bonus
            bot.energy = min(bot.derived.max_energy, bot.energy + energy_restore)


def attribute_kills(
    round_elims: list[_Event], round_events: list[_Event],
    bots: list[Bot], round_num: int,
) -> None:
    """Find killing blow and attribute kills to attackers."""
    for elim in round_elims:
        killer_emoji: str | None = None
        for evt in round_events:
            if (evt.get("type") in _HIT_TYPES and evt.get("target") == elim["emoji"]
                    and evt.get("hp_before", 1) > 0
                    and evt["hp_before"] - evt["damage"] <= 0):
                killer_emoji = evt["attacker"]
                break
        if killer_emoji is None:
            for evt in round_events:
                if evt.get("type") in _HIT_TYPES and evt.get("target") == elim["emoji"]:
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
                    b.energy = min(b.energy + KILL_BOUNTY_ENERGY, b.derived.max_energy)
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
            "emoji": bot.emoji, "glyph": bot.glyph, "x": bot.x, "y": bot.y,
            "hp": bot.hp, "energy": bot.energy,
            "action": action_str, "alive": bot.alive,
            "score": bot.score, "momentum_tier": bot.momentum_tier,
            "is_leader": bot.is_leader,
            "max_hp": bot.derived.max_hp,
        })
    return {"round": round_num, "storm_border": storm_border,
            "positions": positions, "events": events}
