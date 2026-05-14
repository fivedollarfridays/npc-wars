"""Per-event metadata fields: tick_in_round + position.

Additive schema additions per borst RFC (npc-wars#61). Both fields are
strictly optional from a consumer perspective — existing tooling that
doesn't know about them continues to work unchanged.

`tick_in_round` is the phase index from `resolve_combat_phases` (0..12).
`position` is the primary actor's grid coords at the moment the event
fires. Together they let downstream renderers replay phase-ordered,
spatially-grounded timelines instead of fabricating them from round-end
snapshots.
"""

from typing import Any

# Phase indices for tick_in_round (0..12) — matches the order in
# engine.match_phases.resolve_combat_phases. Constants live here (not in
# match_phases) to avoid circular imports back from the per-phase
# resolver modules (rounds, rounds_combat, bumpers, plague).
TICK_TACTICAL = 0
TICK_ABILITY = 1
TICK_DEFENSE = 2
TICK_MOVEMENT = 3
TICK_VERTICALITY = 4
TICK_TRAPS = 5
TICK_TAUNT = 6
TICK_MELEE = 7
TICK_RANGED = 8
TICK_STORM = 9
TICK_PLAGUE = 10
TICK_DEATHS = 11
TICK_MOMENTUM = 12


def position(bot: Any) -> dict[str, int]:
    """Build a position dict from a bot's current grid coords.

    Accepts anything with .x and .y int attributes (Bot, or a duck type
    in tests). Returns {"x": int, "y": int}.
    """
    return {"x": bot.x, "y": bot.y}
