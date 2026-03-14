"""Cringe observer — classifies human action contexts during matches.

Watches each round's events and game state, classifies the context for
each human bot, and records the human's actual action into a PatternTable.
"""

from __future__ import annotations

from typing import Any

from engine.combat import Bot
from engine.watcher_memory import PatternTable

_HIT_TYPES = frozenset({"hit", "ranged_hit"})
_LOW_HP_THRESHOLD = 30


def _was_damaged(human_emoji: str, round_events: list[dict[str, Any]]) -> bool:
    """Check if this human was the target of a hit or ranged_hit."""
    return any(
        e.get("type") in _HIT_TYPES and e.get("target") == human_emoji
        for e in round_events
    )


def _nearest_enemy_distance(human: Bot, bots: list[Bot]) -> int | None:
    """Return Manhattan distance to nearest alive enemy, or None if none."""
    min_dist: int | None = None
    for b in bots:
        if b.emoji == human.emoji or not b.alive:
            continue
        dist = abs(b.x - human.x) + abs(b.y - human.y)
        if min_dist is None or dist < min_dist:
            min_dist = dist
    return min_dist


def _is_near_storm(bot: Bot, storm_border: int, grid_size: int) -> bool:
    """Check if bot is within 2 tiles of the storm border.

    The safe zone spans [storm_border, grid_size - storm_border).
    "Near" means within 2 tiles of the boundary from inside or already in storm.
    """
    margin = 2
    low_threshold = storm_border + margin
    high_threshold = grid_size - storm_border - margin
    return (
        bot.x < low_threshold
        or bot.x >= high_threshold
        or bot.y < low_threshold
        or bot.y >= high_threshold
    )


def classify_contexts(
    human_emoji: str,
    round_events: list[dict[str, Any]],
    bots: list[Bot],
    storm_border: int,
    grid_size: int,
    actions: dict[str, Any],
    bot_decisions: dict[str, Any] | None = None,
    *,
    bot_map: dict[str, Bot] | None = None,
) -> list[str]:
    """Classify which contexts apply to a human bot this round."""
    if bot_map is not None:
        human = bot_map.get(human_emoji)
    else:
        human = next((b for b in bots if b.emoji == human_emoji), None)
    if human is None:
        return []

    contexts: list[str] = []

    # after_damage: was hit this round
    if _was_damaged(human_emoji, round_events):
        contexts.append("after_damage")

    # at_range_1: adjacent to nearest enemy
    dist = _nearest_enemy_distance(human, bots)
    if dist is not None and dist == 1:
        contexts.append("at_range_1")

    # below_30_hp
    if human.hp < _LOW_HP_THRESHOLD:
        contexts.append("below_30_hp")

    # storm_closing: near storm border
    if storm_border > 0 and _is_near_storm(human, storm_border, grid_size):
        contexts.append("storm_closing")

    # override_detected: human action differs from bot decision
    if bot_decisions is not None:
        human_action = actions.get(human_emoji)
        bot_action = bot_decisions.get(human_emoji)
        if human_action is not None and bot_action is not None and human_action != bot_action:
            contexts.append("override_detected")

    return contexts


def observe_round(
    pattern_table: PatternTable,
    human_emojis: list[str],
    round_events: list[dict[str, Any]],
    bots: list[Bot],
    storm_border: int,
    grid_size: int,
    actions: dict[str, Any],
    bot_decisions: dict[str, Any] | None = None,
) -> None:
    """Observe a round and record each human's action for each classified context."""
    bot_map = {b.emoji: b for b in bots}
    for emoji in human_emojis:
        action = actions.get(emoji)
        if action is None:
            continue
        # Normalize action to string (first element of tuple or string)
        action_str = action[0] if isinstance(action, tuple) else str(action)

        contexts = classify_contexts(
            emoji, round_events, bots, storm_border, grid_size, actions, bot_decisions,
            bot_map=bot_map,
        )
        for ctx in contexts:
            pattern_table.record(emoji, ctx, action_str)


__all__ = ["classify_contexts", "observe_round"]
