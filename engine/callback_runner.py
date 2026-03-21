"""Callback execution helpers for the match loop.

Functions that run bot callbacks (setup, react, on_kill) during match
execution. Provides event filtering and safe invocation via execute_callback.
"""

from __future__ import annotations

from typing import Any

from engine.callbacks import execute_callback
from engine.combat import Bot
from engine.state import build_state

__all__ = ["run_react_callbacks", "run_setup_callbacks"]

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
