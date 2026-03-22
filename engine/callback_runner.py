"""Callback execution helpers for the match loop.

Functions that run bot callbacks (setup, react, on_kill) during match
execution. Provides event filtering and safe invocation via execute_callback.
"""

from __future__ import annotations

from typing import Any

import logging

from engine.abilities import validate_ability
from engine.callbacks import execute_callback
from engine.combat import Bot
from engine.state import build_state

__all__ = [
    "check_evolve_trigger", "run_evolve_callbacks",
    "run_on_kill_callbacks", "run_power_up_callbacks",
    "run_react_callbacks", "run_setup_callbacks",
]

_logger = logging.getLogger(__name__)

# Killers with these identifiers are environmental, not player bots.
_NON_BOT_KILLERS: frozenset[str] = frozenset({"storm", "plague", "tiebreaker", "unknown", ""})

def run_on_kill_callbacks(
    bots: list[Bot],
    round_elims: list[dict[str, Any]],
    round_num: int,
    grid_size: int,
    storm_border: int,
) -> None:
    """Call on_kill() for each bot that scored a combat kill this round.

    Environmental kills (storm, plague, tiebreaker) are skipped.
    Exceptions in any bot's on_kill are caught by execute_callback.
    """
    emoji_to_bot: dict[str, Bot] = {b.emoji: b for b in bots}

    for elim in round_elims:
        killer_emoji = elim.get("killed_by", "")
        if killer_emoji in _NON_BOT_KILLERS:
            continue
        killer = emoji_to_bot.get(killer_emoji)
        if killer is None:
            continue
        if killer.callbacks.on_kill is None:
            continue
        state = build_state(killer, bots, round_num=round_num,
                            grid_size=grid_size, storm_border=storm_border)
        victim_emoji = elim["emoji"]
        execute_callback(killer.callbacks.on_kill, state, victim_emoji)


def run_setup_callbacks(
    bots: list[Bot], grid_size: int, storm_border: int,
) -> None:
    """Call each bot's setup callback once before round 1.

    Builds a state dict matching the shape of decide()'s state
    (via build_state) with round=0 to indicate pre-match.
    Bots without a setup callback are skipped.
    Exceptions in any bot's setup are caught by execute_callback.
    """
    for bot in bots:
        if bot.callbacks.setup is None:
            continue
        state = build_state(bot, bots, round_num=0, grid_size=grid_size,
                            storm_border=storm_border)
        execute_callback(bot.callbacks.setup, state)


def run_power_up_callbacks(
    bots: list[Bot], grid_size: int, storm_border: int,
) -> None:
    """Call each bot's power_up callback once to define their custom ability.

    The callback receives a state dict and should return an ability definition
    dict. Invalid results are silently ignored (bot gets no ability).
    """
    for bot in bots:
        if bot.callbacks.power_up is None:
            continue
        state = build_state(bot, bots, round_num=0, grid_size=grid_size,
                            storm_border=storm_border)
        try:
            result = bot.callbacks.power_up(state)
        except Exception:
            _logger.debug("power_up callback raised for %s", bot.emoji, exc_info=True)
            continue
        ability_def = validate_ability(result)
        if ability_def is not None:
            bot.ability = ability_def


_REACT_RADIUS = 3


def _build_nearby_events(
    bot: Bot, round_events: list[dict[str, Any]], all_bots: list[Bot],
) -> list[dict[str, Any]]:
    """Filter round events to those within 3 Manhattan tiles of *bot*.

    An event is considered nearby if any bot emoji referenced in the event
    (attacker, target, emoji fields) is within range of the bot.
    """
    emoji_to_pos: dict[str, tuple[int, int]] = {
        b.emoji: (b.x, b.y) for b in all_bots
    }
    bx, by = bot.x, bot.y
    nearby: list[dict[str, Any]] = []

    for event in round_events:
        # Check all emoji-reference fields in the event
        for key in ("attacker", "target", "emoji", "victim", "owner"):
            ref = event.get(key)
            if ref is not None and ref in emoji_to_pos:
                ex, ey = emoji_to_pos[ref]
                if abs(bx - ex) + abs(by - ey) <= _REACT_RADIUS:
                    nearby.append(event)
                    break  # Don't add same event twice

    return nearby


def run_react_callbacks(
    bots: list[Bot],
    round_events: list[dict[str, Any]],
    grid_size: int,
    storm_border: int,
    round_num: int,
) -> None:
    """Call react() for every alive bot that has the callback.

    Each bot receives its own state dict and a filtered list of nearby events.
    Exceptions are caught by execute_callback -- a bad react() never crashes
    the match.
    """
    for bot in bots:
        if not bot.alive:
            continue
        if bot.callbacks.react is None:
            continue
        state = bot.to_self_dict()
        state["round"] = round_num
        state["grid_size"] = grid_size
        state["storm_border"] = storm_border
        enemies = [
            b.to_enemy_dict()
            for b in bots
            if b.emoji != bot.emoji and b.alive
        ]
        state["enemies"] = enemies
        nearby = _build_nearby_events(bot, round_events, bots)
        execute_callback(bot.callbacks.react, state, nearby)


_EVOLVE_KILL_THRESHOLD = 3
_EVOLVE_ROUND_THRESHOLD = 20


def check_evolve_trigger(bot: Bot, round_num: int) -> bool:
    """Return True if evolve trigger condition is met.

    Fires when bot has 3+ kills OR round >= 20, whichever comes first.
    """
    return bot.kills >= _EVOLVE_KILL_THRESHOLD or round_num >= _EVOLVE_ROUND_THRESHOLD


_EVOLVE_STAT_NAMES = ("power", "speed", "armor", "mind")
_EVOLVE_MAX_SHIFT = 10
_EVOLVE_MAX_ABILITY_BOOST = 15


def _validate_stat_shift(shift: Any) -> dict[str, int] | None:
    """Validate stat_shift: must be dict, sum to 0, each abs <= 10."""
    if not isinstance(shift, dict):
        return None
    total = 0
    clean: dict[str, int] = {}
    for key, val in shift.items():
        if key not in _EVOLVE_STAT_NAMES:
            return None
        if not isinstance(val, int):
            return None
        if abs(val) > _EVOLVE_MAX_SHIFT:
            return None
        total += val
        clean[key] = val
    if total != 0:
        return None
    return clean


def _apply_stat_shift(bot: Bot, shift: dict[str, int]) -> None:
    """Apply validated stat shift to bot, creating new StatAllocation."""
    from engine.stats import StatAllocation, calculate_derived
    new_stats = StatAllocation(
        power=bot.stats.power + shift.get("power", 0),
        speed=bot.stats.speed + shift.get("speed", 0),
        armor=bot.stats.armor + shift.get("armor", 0),
        mind=bot.stats.mind + shift.get("mind", 0),
    )
    bot.stats = new_stats
    bot.derived = calculate_derived(new_stats)


def _apply_ability_boost(bot: Bot, boost: int) -> None:
    """Apply ability potency boost (capped at 15). Creates new frozen AbilityDef."""
    if bot.ability is None:
        return
    from engine.abilities import AbilityDef
    capped = min(boost, _EVOLVE_MAX_ABILITY_BOOST)
    bot.ability = AbilityDef(
        name=bot.ability.name, type=bot.ability.type,
        potency=bot.ability.potency + capped,
        range=bot.ability.range, cooldown=bot.ability.cooldown,
        energy_cost=bot.ability.energy_cost,
    )


def run_evolve_callbacks(
    bots: list[Bot], round_num: int, grid_size: int, storm_border: int,
) -> list[dict[str, Any]]:
    """Call evolve() for eligible bots. Returns list of evolve events."""
    events: list[dict[str, Any]] = []
    for bot in bots:
        if not bot.alive or bot.has_evolved:
            continue
        if bot.callbacks.evolve is None:
            continue
        if not check_evolve_trigger(bot, round_num):
            continue
        state = build_state(bot, bots, round_num=round_num,
                            grid_size=grid_size, storm_border=storm_border)
        try:
            result = bot.callbacks.evolve(state)
        except Exception:
            _logger.debug("evolve callback raised for %s", bot.emoji, exc_info=True)
            bot.has_evolved = True
            continue
        if not isinstance(result, dict):
            bot.has_evolved = True
            continue
        event: dict[str, Any] = {"type": "evolve", "emoji": bot.emoji}
        # Apply stat_shift
        raw_shift = result.get("stat_shift")
        if raw_shift is not None:
            validated = _validate_stat_shift(raw_shift)
            if validated:
                _apply_stat_shift(bot, validated)
                event["stat_shift"] = validated
        # Apply ability_boost
        raw_boost = result.get("ability_boost")
        if isinstance(raw_boost, int) and raw_boost > 0:
            _apply_ability_boost(bot, raw_boost)
            capped = min(raw_boost, _EVOLVE_MAX_ABILITY_BOOST)
            event["ability_boost"] = capped
        bot.has_evolved = True
        events.append(event)
    return events
