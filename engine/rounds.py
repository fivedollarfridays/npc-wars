"""Per-round phase helpers for the match engine.

This module is the public entry point. Heavy phase logic lives in
sibling modules and is re-exported here for backward compatibility:

- ``engine.rounds_decisions``  — decision phase, taunt/copilot overrides
- ``engine.rounds_movement``   — move/dash phase, terrain effects
- ``engine.rounds_combat``     — melee/ranged attack phases
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.terrain import TerrainMap

from engine.combat import (
    Bot, STORM_DAMAGE, REST_HEAL, REST_ENERGY_RESTORE, DEFEND_BONUS,
    STARTING_DEFENSE,
    KILL_BOUNTY_ENERGY, TAUNT_RANGE,
)
from engine.grid import is_in_storm, storm_depth  # noqa: F401
from engine.terrain_combat import can_rest_heal
from engine.rounds_combat import (  # noqa: F401 — re-exported for backward compat
    resolve_attacks, resolve_ranged_attacks, build_pos_map,
)
from engine.rounds_decisions import (  # noqa: F401 — re-exported for backward compat
    resolve_decisions, _apply_taunt_override,
)
from engine.rounds_movement import (  # noqa: F401 — re-exported for backward compat
    resolve_movement,
)
from engine.event_meta import (
    TICK_DEFENSE, TICK_STORM, TICK_DEATHS, position,
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


def resolve_defense(alive_bots: list[Bot], actions: _ActionsMap) -> list[_Event]:
    """Phase 2: Reset and apply defense bonuses; emit defend events."""
    events: list[_Event] = []
    for bot in alive_bots:
        bot.defense = STARTING_DEFENSE
        action = actions.get(bot.emoji)
        if action and action[0] == "defend":
            bot.defense = DEFEND_BONUS
            events.append({
                "type": "defend", "emoji": bot.emoji,
                "tick_in_round": TICK_DEFENSE, "position": position(bot),
            })
    return events


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
    """Phase 5: Apply depth-scaled storm damage. Deeper = more damage."""
    events: list[_Event] = []
    for bot in alive_bots:
        if not bot.alive:
            continue
        depth = storm_depth(bot.x, bot.y, grid_size, storm_border)
        if depth > 0:
            # Base 10 + 3 per tile of depth, with fractional component for tiebreaking
            damage = STORM_DAMAGE + (depth - 1) * 3.0 + depth * 0.1
            bot.hp -= damage
            bot.damage_taken += int(damage)
            events.append({
                "type": "storm_damage", "target": bot.emoji,
                "damage": round(damage, 1), "depth": depth,
                "tick_in_round": TICK_STORM, "position": position(bot),
            })
    return events


def apply_energy_and_rest(
    alive_bots: list[Bot], actions: _ActionsMap, forced_rest: set[str],
    terrain: TerrainMap | None = None,
) -> None:
    """Phase 6+7: Deduct energy costs and apply explicit rest healing."""
    for bot in alive_bots:
        action = actions.get(bot.emoji)
        if action and action[0] not in ("nothing", "disconnected") and bot.emoji not in forced_rest:
            bot.apply_action_cost(action[0])
    for bot in alive_bots:
        action = actions.get(bot.emoji)
        if action and action[0] == "rest":
            if can_rest_heal(terrain, bot.x, bot.y):
                bot.hp = min(float(bot.derived.max_hp), bot.hp + REST_HEAL)
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
                if (evt.get("type") == "trap_trigger" and evt.get("victim") == elim["emoji"]
                        and evt.get("hp_before", 1) > 0
                        and evt["hp_before"] - evt["damage"] <= 0):
                    killer_emoji = evt["owner"]
                    break
        if killer_emoji is None:
            for evt in round_events:
                if evt.get("type") == "trap_trigger" and evt.get("victim") == elim["emoji"]:
                    killer_emoji = evt["owner"]
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
        victim_pos: dict[str, int] | None = None
        for b in bots:
            if b.emoji == elim["emoji"]:
                victim_pos = position(b)
                break
        round_events.append({
            "type": "kill", "attacker": killer_emoji or "unknown",
            "victim": elim["emoji"], "round": round_num,
            "tick_in_round": TICK_DEATHS, "position": victim_pos,
        })


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
