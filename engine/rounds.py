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
    STARTING_DEFENSE, TAUNT_RANGE,
)
from engine.grid import is_clamp_induced, is_in_storm, storm_depth  # noqa: F401
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
from engine.rounds_upkeep import attribute_kills  # noqa: F401 — re-exported for backward compat
from engine.event_meta import (
    TICK_DEFENSE, TICK_STORM, position,
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


def _storm_damage_event(bot: Bot, damage: float, depth: int) -> _Event:
    """Apply *damage* to *bot* and build the storm_damage event."""
    bot.hp -= damage
    bot.damage_taken += int(damage)
    return {
        "type": "storm_damage", "target": bot.emoji,
        "damage": round(damage, 1), "depth": depth,
        "tick_in_round": TICK_STORM, "position": position(bot),
    }


def apply_storm_damage(
    alive_bots: list[Bot], grid_size: int, storm_border: int, round_num: int = 0,
) -> list[_Event]:
    """Phase 5: Apply depth-scaled storm damage. Deeper = more damage.

    Endgame forced resolution: when the safe zone exists ONLY because of the
    2x2 clamp (``is_clamp_induced``), bots inside the safe zone (depth 0) also
    take base storm damage so an evading low-hp bot cannot dodge to the cap.
    """
    clamp_induced = is_clamp_induced(round_num, grid_size)
    events: list[_Event] = []
    for bot in alive_bots:
        if not bot.alive:
            continue
        depth = storm_depth(bot.x, bot.y, grid_size, storm_border)
        if depth > 0:
            # Base 10 + 3 per tile of depth, with fractional component for tiebreaking
            damage = STORM_DAMAGE + (depth - 1) * 3.0 + depth * 0.1
            events.append(_storm_damage_event(bot, damage, depth))
        elif clamp_induced:
            events.append(_storm_damage_event(bot, float(STORM_DAMAGE), 1))
    return events


def apply_energy_and_rest(
    alive_bots: list[Bot], actions: _ActionsMap, forced_rest: set[str],
    terrain: TerrainMap | None = None,
    grid_size: int | None = None, storm_border: int = 0,
    round_num: int = 0,
) -> None:
    """Phase 6+7: Deduct energy costs and apply explicit rest healing.

    Resting inside the storm restores energy but NOT hp (endgame fix): when
    *grid_size* is given and the bot is in the storm, the hp heal is skipped.

    Deep endgame: when the safe zone exists ONLY because of the 2x2 clamp
    (``is_clamp_induced``), rest restores energy but NOT hp even inside the
    safe zone, so the final bots cannot rest-camp to the round cap.
    """
    clamp_induced = grid_size is not None and is_clamp_induced(round_num, grid_size)
    for bot in alive_bots:
        action = actions.get(bot.emoji)
        if action and action[0] not in ("nothing", "disconnected") and bot.emoji not in forced_rest:
            bot.apply_action_cost(action[0])
    for bot in alive_bots:
        action = actions.get(bot.emoji)
        if action and action[0] == "rest":
            in_storm = (
                grid_size is not None
                and is_in_storm(bot.x, bot.y, grid_size, storm_border)
            )
            if not in_storm and not clamp_induced and can_rest_heal(terrain, bot.x, bot.y):
                bot.hp = min(float(bot.derived.max_hp), bot.hp + REST_HEAL)
            eq = bot.equipment_bonuses
            energy_restore = (
                REST_ENERGY_RESTORE + bot.derived.energy_regen + bot.momentum_energy_bonus
                + eq.energy_regen + eq.rest_energy_bonus
            )
            bot.energy = min(bot.derived.max_energy, bot.energy + energy_restore)


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
