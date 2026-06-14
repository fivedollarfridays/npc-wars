"""Decision-phase helpers extracted from rounds.py.

Handles per-bot action collection: copilot human overrides, taunt
redirection, and the main decision loop that calls each bot's strategy.
"""

from __future__ import annotations

from typing import Any

from engine.combat import Bot, MAX_CONSECUTIVE_FAILURES
from engine.grid import direction_toward
from engine.state import build_state
from engine.sandbox import LOCKED, classify_action, execute_decide, validate_action

__all__ = ["resolve_decisions", "_apply_taunt_override"]

_Action = tuple[str, ...]
_ActionsMap = dict[str, _Action]
_Event = dict[str, Any]


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


def _degrade_locked(
    bot: Bot, raw_action: Any, actions: _ActionsMap,
    override_events: list[_Event],
) -> None:
    """Locked-but-well-formed action: rest, emit event, no failure penalty."""
    attempted = raw_action[0]
    actions[bot.emoji] = ("rest",)
    bot.consecutive_failures = 0
    override_events.append({
        "type": "locked_action",
        "player": bot.emoji,
        "action": attempted,
    })


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
        classified = classify_action(raw_action, set(bot.unlocked_actions))

        if classified is LOCKED:
            _degrade_locked(bot, raw_action, actions, override_events)
            continue

        # LOCKED handled above: narrow classified to tuple|None for the typer.
        assert classified is None or isinstance(classified, tuple)
        action = _apply_human_override(bot, state, classified, override_events)

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
