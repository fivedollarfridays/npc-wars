"""Async match engine for NPC Wars (human/copilot mode)."""

import asyncio
from pathlib import Path
from typing import Any

from engine.combat import Bot, STARTING_ATTACK_POWER, get_round_bonus_attack
from engine.match_modes import get_mode, get_storm_border_for_mode
from engine.spectacle import SpectacleEngine
from engine.discord_integration import notify_match_start
from engine.game import (
    _apply_momentum_phase, _execute_round, _finalize_match,
    _prepare_match, _resolve_combat_phases, _score_spectacle,
)

__all__ = ["run_match_async"]


async def _collect_human_override(
    bot: Bot, state: dict[str, Any], timeout_s: float,
) -> tuple[str, tuple[str, ...] | None]:
    """Collect one human's async input. Returns (emoji, action_or_None).

    The outer ``wait_for`` is the authoritative timeout; the adapter receives
    ``float('inf')`` so it does not race with a second timer.
    """
    try:
        raw = await asyncio.wait_for(
            bot.human_adapter.get_action_async(state, float("inf")),  # type: ignore[union-attr]
            timeout=timeout_s,
        )
    except asyncio.TimeoutError:
        raw = None
    return bot.emoji, raw


async def _execute_round_async(
    bots: list[Bot], round_num: int, grid_size: int, storm_border: int,
    bumps_last_round: list[dict[str, Any]] | None = None,
    human_timeout: float = 2.0,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], set[str]]:
    """Async round: gathers human inputs concurrently after bot decisions."""
    from engine.combat import MAX_CONSECUTIVE_FAILURES
    from engine.sandbox import execute_decide, validate_action
    from engine.state import build_state

    alive_bots = [b for b in bots if b.alive]
    emoji_to_bot = {b.emoji: b for b in alive_bots}

    bonus = get_round_bonus_attack(round_num)
    for bot in alive_bots:
        bot.attack_power = STARTING_ATTACK_POWER + bonus

    actions: dict[str, tuple[str, ...]] = {}
    forced_rest: set[str] = set()
    human_bots: list[tuple[Bot, dict[str, Any]]] = []
    override_events: list[dict[str, Any]] = []

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
        actions[bot.emoji] = action if action is not None else ("nothing",)
        if bot.human_adapter is not None:
            human_bots.append((bot, state))

    human_responded: set[str] = set()
    if human_bots:
        tasks = [
            _collect_human_override(bot, st, human_timeout)
            for bot, st in human_bots
        ]
        results = await asyncio.gather(*tasks)
        for emoji, human_raw in results:
            if human_raw is not None:
                human_action = validate_action(
                    human_raw, unlocked_actions=set(emoji_to_bot[emoji].unlocked_actions),
                )
                if human_action is not None:
                    original = actions[emoji]
                    if human_action != original:
                        override_events.append({
                            "type": "human_override",
                            "player": emoji,
                            "original": " ".join(original),
                            "override": " ".join(human_action),
                        })
                    actions[emoji] = human_action
                    human_responded.add(emoji)

    for bot in alive_bots:
        if bot.emoji in forced_rest:
            continue
        act = actions[bot.emoji]
        if act[0] == "nothing":
            bot.consecutive_failures += 1
            if bot.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                bot.hp = 0
                actions[bot.emoji] = ("disconnected",)
        else:
            bot.consecutive_failures = 0

    round_data, round_elims, bump_events = _resolve_combat_phases(
        alive_bots, bots, actions, forced_rest, override_events,
        round_num, grid_size, storm_border,
    )
    return round_data, round_elims, bump_events, human_responded


async def run_match_async(
    bot_configs: list[dict[str, Any]], match_id: int = 1, seed: int | None = None,
    profiles_path: Path | None = None, human_timeout: float = 2.0,
    match_mode: str = "standard",
) -> dict[str, Any]:
    """Async match loop. Uses async rounds when humans are present."""
    from engine.afk import AFKTracker
    from engine.watcher_controller import WatcherController

    mode = get_mode(match_mode)
    bots, players, grid_size, rng = _prepare_match(bot_configs, seed, mode=mode)
    has_humans = any(b.human_adapter is not None for b in bots)
    afk_tracker = AFKTracker()
    for b in bots:
        if b.human_adapter is not None:
            afk_tracker.register(b.emoji)
    notify_match_start(match_id=match_id, players=players, seed=seed)

    watcher_ctrl: WatcherController | None = None
    if has_humans:
        watcher_ctrl = WatcherController(rng=rng)

    all_rounds: list[dict[str, Any]] = []
    all_eliminations: list[dict[str, Any]] = []
    last_bump_events: list[dict[str, Any]] = []
    spectacle_engine = SpectacleEngine()
    prev_storm_border = 0

    for round_num in range(1, mode.max_rounds + 1):
        if sum(b.alive for b in bots) <= 1:
            break

        storm_border = get_storm_border_for_mode(round_num, mode)

        spawn_events: list[dict[str, Any]] = []
        if watcher_ctrl is not None:
            spawn_events = watcher_ctrl.try_spawn(bots, round_num, grid_size, storm_border)

        if has_humans:
            round_data, round_elims, last_bump_events, responded = await _execute_round_async(
                bots, round_num, grid_size, storm_border,
                bumps_last_round=last_bump_events, human_timeout=human_timeout,
            )
            if spawn_events:
                round_data.setdefault("events", []).extend(spawn_events)
            if watcher_ctrl is not None:
                watcher_ctrl.post_round(
                    bots, round_data, round_elims, round_num, grid_size, storm_border,
                )
            for b in bots:
                if b.human_adapter is not None:
                    if b.emoji in responded:
                        afk_tracker.record_input(b.emoji)
                    else:
                        afk_tracker.record_miss(b.emoji)
                        if afk_tracker.is_kicked(b.emoji):
                            b.human_adapter = None
        else:
            round_data, round_elims, last_bump_events = _execute_round(
                bots, round_num, grid_size, storm_border,
                bumps_last_round=last_bump_events,
            )

        _apply_momentum_phase(bots, round_data, round_num, storm_border, prev_storm_border)
        _score_spectacle(spectacle_engine, round_data, bots)
        all_rounds.append(round_data)
        all_eliminations.extend(round_elims)
        prev_storm_border = storm_border

        if sum(b.alive for b in bots) <= 1:
            break
    else:
        round_num = mode.max_rounds

    if watcher_ctrl is not None:
        winner_alive = [b for b in bots if b.alive]
        watcher_won = (
            watcher_ctrl.watcher_bot is not None
            and watcher_ctrl.watcher_bot.alive
            and len(winner_alive) <= 1
        )
        watcher_ctrl.finalize(won=watcher_won)

    return _finalize_match(
        bots, players, all_rounds, all_eliminations,
        round_num, match_id, grid_size, profiles_path,
        match_mode=mode.name,
    )
