"""Main match engine for NPC Wars."""

import asyncio
import random
from pathlib import Path
from typing import Any

from engine.combat import Bot, resolve_deaths, STARTING_ATTACK_POWER, get_round_bonus_attack, tick_damage_bonus
from engine.grid import calculate_grid_size, spawn_positions
from engine.match_modes import MatchMode, get_mode, get_storm_border_for_mode
from engine.match_writer import build_match_data
from engine.discord_integration import notify_match_start, notify_match_end
from engine.spectacle import SpectacleEngine
from data.player_profiles import update_profiles_after_match
from engine.rounds import (
    resolve_decisions, resolve_defense, resolve_movement,
    resolve_attacks, resolve_ranged_attacks, resolve_taunt,
    apply_storm_damage, apply_energy_and_rest,
    attribute_kills, build_round_record, build_pos_map,
)

__all__ = ["MAX_ROUNDS", "run_match", "run_match_async"]

MAX_ROUNDS = 200  # Safety limit

_PROGRESSION_FIELDS = ("unlocked_actions", "line_budget", "win_streak")


def _create_bots(
    bot_configs: list[dict[str, Any]], positions: list[tuple[int, int]],
) -> list[Bot]:
    """Create Bot instances from configs and spawn positions."""
    bots = []
    for i, config in enumerate(bot_configs):
        x, y = positions[i]
        bot_obj = Bot(
            name=config["name"], emoji=config["emoji"],
            bio=config["bio"], author=config.get("author", "unknown"),
            decide_func=config["decide_func"], x=x, y=y,
        )
        for fld in _PROGRESSION_FIELDS:
            if fld in config:
                setattr(bot_obj, fld, config[fld])
        if "human_adapter" in config:
            bot_obj.human_adapter = config["human_adapter"]
        bots.append(bot_obj)
    return bots


def _resolve_tiebreaker(
    bots: list[Bot], round_num: int, all_eliminations: list[dict[str, Any]],
) -> str:
    """Determine winner with tiebreaker if multiple bots survive."""
    still_alive = [b for b in bots if b.alive]
    if len(still_alive) > 1:
        still_alive.sort(key=lambda b: (b.hp, b.energy, b.kills, b.damage_dealt), reverse=True)
        for loser in still_alive[1:]:
            loser.alive = False
            all_eliminations.append({"emoji": loser.emoji, "round": round_num,
                                     "killed_by": "tiebreaker", "cause": "tiebreaker"})
        return still_alive[0].emoji
    if still_alive:
        return still_alive[0].emoji
    return "none"


def _resolve_combat_phases(
    alive_bots: list[Bot], bots: list[Bot], actions: dict[str, tuple[str, ...]],
    forced_rest: set[str], override_events: list[dict[str, Any]],
    round_num: int, grid_size: int, storm_border: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Phases 2-7: defense, movement, attacks, storm, energy, deaths."""
    resolve_defense(alive_bots, actions)
    bump_events = resolve_movement(
        alive_bots, actions, grid_size, all_bots=bots, storm_border=storm_border,
    )
    taunt_events = resolve_taunt(alive_bots, actions)
    pos_map = build_pos_map(alive_bots)
    round_events = override_events + bump_events + resolve_attacks(alive_bots, actions, pos_map)
    round_events.extend(taunt_events)
    round_events.extend(resolve_ranged_attacks(alive_bots, actions, pos_map))
    round_events.extend(apply_storm_damage(alive_bots, grid_size, storm_border))
    apply_energy_and_rest(alive_bots, actions, forced_rest)

    round_elims = resolve_deaths(bots, round_num)
    attribute_kills(round_elims, round_events, bots, round_num)
    tick_damage_bonus(alive_bots)

    for bot in alive_bots:
        if bot.alive:
            bot.rounds_survived = round_num

    round_data = build_round_record(bots, actions, round_num, storm_border, round_events)
    return round_data, round_elims, bump_events


def _prepare_match(
    bot_configs: list[dict[str, Any]], seed: int | None, mode: MatchMode | None = None,
) -> tuple[list[Bot], list[dict[str, Any]], int, random.Random]:
    """Shared match setup: RNG, grid, bots, players. Returns (bots, players, grid_size, rng)."""
    rng = random.Random(seed)
    grid_size = calculate_grid_size(len(bot_configs))
    positions = spawn_positions(len(bot_configs), grid_size, rng)
    bots = _create_bots(bot_configs, positions)
    if mode is not None and mode.starting_hp != 100:
        for b in bots:
            b.hp = mode.starting_hp
    players = [{"emoji": b.emoji, "name": b.name, "bio": b.bio, "author": b.author} for b in bots]
    return bots, players, grid_size, rng


def _finalize_match(
    bots: list[Bot], players: list[dict[str, Any]], all_rounds: list[dict[str, Any]],
    all_eliminations: list[dict[str, Any]], round_num: int, match_id: int,
    grid_size: int, profiles_path: Path | None, match_mode: str = "standard",
) -> dict[str, Any]:
    """Shared post-loop: tiebreaker, stats, match data, notifications."""
    winner_emoji = _resolve_tiebreaker(bots, round_num, all_eliminations)
    stats = {b.emoji: {"kills": b.kills, "damage_dealt": b.damage_dealt,
                        "damage_taken": b.damage_taken, "rounds_survived": b.rounds_survived}
             for b in bots}

    match_data = build_match_data(
        match_id=match_id, grid_size=grid_size, players=players,
        rounds=all_rounds, eliminations=all_eliminations,
        winner_emoji=winner_emoji, stats=stats, duration_rounds=round_num,
    )
    match_data["match_mode"] = match_mode
    notify_match_end(match_data)

    if profiles_path is not None:
        update_profiles_after_match(profiles_path, players, winner_emoji)

    return match_data


def _score_spectacle(
    spectacle_engine: SpectacleEngine, round_data: dict[str, Any], bots: list[Bot],
) -> None:
    """Score drama for a round and attach spectacle data."""
    bot_states = [{"emoji": b.emoji, "hp": b.hp, "alive": b.alive} for b in bots]
    sd = spectacle_engine.score_round(round_data.get("events", []), bot_states)
    round_data["spectacle"] = {
        "drama_score": sd.drama_score, "tier": sd.tier,
        "triggers": sd.triggers, "effects": sd.effects,
    }


def _execute_round(
    bots: list[Bot], round_num: int, grid_size: int, storm_border: int,
    bumps_last_round: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Execute one round of the match. Returns (round_data, eliminations, bump_events)."""
    alive_bots = [b for b in bots if b.alive]

    bonus = get_round_bonus_attack(round_num)
    for bot in alive_bots:
        bot.attack_power = STARTING_ATTACK_POWER + bonus

    actions, forced_rest, override_events = resolve_decisions(
        alive_bots, bots, round_num, grid_size, storm_border,
        bumps_last_round=bumps_last_round,
    )
    return _resolve_combat_phases(
        alive_bots, bots, actions, forced_rest, override_events,
        round_num, grid_size, storm_border,
    )


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
    """Async round: gathers human inputs concurrently after bot decisions.

    Returns (round_data, eliminations, bump_events, human_responded_emojis).
    """
    from engine.combat import MAX_CONSECUTIVE_FAILURES
    from engine.sandbox import execute_decide, validate_action
    from engine.state import build_state

    alive_bots = [b for b in bots if b.alive]
    emoji_to_bot = {b.emoji: b for b in alive_bots}

    bonus = get_round_bonus_attack(round_num)
    for bot in alive_bots:
        bot.attack_power = STARTING_ATTACK_POWER + bonus

    # Phase 1a: collect bot decisions (sync)
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

    # Phase 1b: gather human overrides concurrently
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

    # Handle consecutive failures
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

    for round_num in range(1, mode.max_rounds + 1):
        if sum(b.alive for b in bots) <= 1:
            break

        storm_border = get_storm_border_for_mode(round_num, mode)

        # Watcher spawn check (before decisions)
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

        _score_spectacle(spectacle_engine, round_data, bots)
        all_rounds.append(round_data)
        all_eliminations.extend(round_elims)

        if sum(b.alive for b in bots) <= 1:
            break
    else:
        round_num = mode.max_rounds

    # Finalize watcher persistence
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


def run_match(
    bot_configs: list[dict[str, Any]], match_id: int = 1, seed: int | None = None,
    profiles_path: Path | None = None, match_mode: str = "standard",
) -> dict[str, Any]:
    """Run a complete match. Returns match data dict."""
    mode = get_mode(match_mode)
    bots, players, grid_size, _rng = _prepare_match(bot_configs, seed, mode=mode)
    notify_match_start(match_id=match_id, players=players, seed=seed)

    all_rounds: list[dict[str, Any]] = []
    all_eliminations: list[dict[str, Any]] = []
    last_bump_events: list[dict[str, Any]] = []
    spectacle_engine = SpectacleEngine()

    for round_num in range(1, mode.max_rounds + 1):
        if sum(b.alive for b in bots) <= 1:
            break

        storm_border = get_storm_border_for_mode(round_num, mode)
        round_data, round_elims, last_bump_events = _execute_round(
            bots, round_num, grid_size, storm_border,
            bumps_last_round=last_bump_events,
        )
        _score_spectacle(spectacle_engine, round_data, bots)
        all_rounds.append(round_data)
        all_eliminations.extend(round_elims)

        if sum(b.alive for b in bots) <= 1:
            break
    else:
        round_num = mode.max_rounds

    return _finalize_match(
        bots, players, all_rounds, all_eliminations,
        round_num, match_id, grid_size, profiles_path,
        match_mode=mode.name,
    )
