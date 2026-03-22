"""Main match engine for NPC Wars."""

import random
from pathlib import Path
from typing import Any

from engine.combat import Bot, STARTING_ATTACK_POWER, get_round_bonus_attack
from engine.grid import calculate_grid_size, spawn_positions
from engine.match_modes import MatchMode, get_mode, get_storm_border_for_mode
from engine.match_writer import build_match_data
from engine.discord_integration import notify_match_start, notify_match_end
from engine.callback_runner import (
    run_evolve_callbacks, run_power_up_callbacks,
    run_react_callbacks, run_setup_callbacks,
)
from engine.spectacle import SpectacleEngine
from engine.archetype import classify_archetype
from engine.terrain import build_map
from engine.traps import TrapManager
from engine.momentum import calculate_carryover, get_tier_name
from data.player_profiles import update_profiles_after_match
from engine.rounds import resolve_decisions
from engine.callbacks import discover_callbacks  # noqa: F401  (re-export for tests)

# Extracted modules
from engine.match_setup import create_bots
from engine.match_phases import (
    apply_momentum_phase,
    resolve_combat_phases,
    score_spectacle,
)

# Backward-compatible aliases (used by game_async.py and tests)
_create_bots = create_bots
_resolve_combat_phases = resolve_combat_phases
_apply_momentum_phase = apply_momentum_phase
_score_spectacle = score_spectacle

__all__ = ["MAX_ROUNDS", "run_match", "run_match_async"]


async def run_match_async(
    bot_configs: list[dict[str, Any]], match_id: int = 1, seed: int | None = None,
    profiles_path: Path | None = None, human_timeout: float = 2.0,
    match_mode: str = "standard",
) -> dict[str, Any]:
    """Async match loop -- delegates to engine.game_async."""
    from engine.game_async import run_match_async as _impl
    return await _impl(
        bot_configs, match_id=match_id, seed=seed,
        profiles_path=profiles_path, human_timeout=human_timeout,
        match_mode=match_mode,
    )

MAX_ROUNDS = 200  # Safety limit


def _prepare_match(
    bot_configs: list[dict[str, Any]], seed: int | None,
    mode: MatchMode | None = None,
) -> tuple[list[Bot], list[dict[str, Any]], int, random.Random]:
    """Shared match setup: RNG, grid, bots, players. Returns (bots, players, grid_size, rng)."""
    rng = random.Random(seed)
    grid_size = calculate_grid_size(len(bot_configs))
    positions = spawn_positions(len(bot_configs), grid_size, rng)
    bots = _create_bots(bot_configs, positions)
    if mode is not None and mode.starting_hp != 100:
        for b in bots:
            b.hp = mode.starting_hp
    players = [{"emoji": b.emoji, "name": b.name, "bio": b.bio, "author": b.author, "glyph": b.glyph} for b in bots]
    return bots, players, grid_size, rng


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


def _finalize_match(
    bots: list[Bot], players: list[dict[str, Any]], all_rounds: list[dict[str, Any]],
    all_eliminations: list[dict[str, Any]], round_num: int, match_id: int,
    grid_size: int, profiles_path: Path | None, match_mode: str = "standard",
) -> dict[str, Any]:
    """Shared post-loop: tiebreaker, stats, match data, notifications."""
    winner_emoji = _resolve_tiebreaker(bots, round_num, all_eliminations)
    stats = {b.emoji: {"kills": b.kills, "damage_dealt": b.damage_dealt,
                        "damage_taken": b.damage_taken, "rounds_survived": b.rounds_survived,
                        "score": b.score,
                        "momentum_tier": b.momentum_tier,
                        "momentum_name": get_tier_name(b.score),
                        "archetype": classify_archetype(b.stats)}
             for b in bots}

    # Carryover: winner gets 50% of score, capped at 50
    carryover: dict[str, int] = {}
    if winner_emoji != "none":
        winner_bot = next((b for b in bots if b.emoji == winner_emoji), None)
        if winner_bot is not None:
            carryover[winner_emoji] = calculate_carryover(winner_bot.score, is_winner=True)

    match_data = build_match_data(
        match_id=match_id, grid_size=grid_size, players=players,
        rounds=all_rounds, eliminations=all_eliminations,
        winner_emoji=winner_emoji, stats=stats, duration_rounds=round_num,
        carryover=carryover,
    )
    match_data["match_mode"] = match_mode
    notify_match_end(match_data)

    if profiles_path is not None:
        update_profiles_after_match(profiles_path, players, winner_emoji)

    return match_data


def _execute_round(
    bots: list[Bot], round_num: int, grid_size: int, storm_border: int,
    bumps_last_round: list[dict[str, Any]] | None = None,
    rng: random.Random | None = None,
    trap_manager: TrapManager | None = None,
    terrain: Any | None = None,
    collected_crystals: set[tuple[int, int]] | None = None,
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
    return resolve_combat_phases(
        alive_bots, bots, actions, forced_rest, override_events,
        round_num, grid_size, storm_border, rng=rng,
        trap_manager=trap_manager,
        terrain=terrain, collected_crystals=collected_crystals,
    )


def run_match(
    bot_configs: list[dict[str, Any]], match_id: int = 1, seed: int | None = None,
    profiles_path: Path | None = None, match_mode: str = "standard",
    map_name: str = "arena",
) -> dict[str, Any]:
    """Run a complete match. Returns match data dict."""
    mode = get_mode(match_mode)
    bots, players, grid_size, rng = _prepare_match(bot_configs, seed, mode=mode)
    terrain = build_map(map_name, grid_size)
    for b in bots:
        b._terrain = terrain
    notify_match_start(match_id=match_id, players=players, seed=seed)

    run_setup_callbacks(bots, grid_size=grid_size, storm_border=0)
    run_power_up_callbacks(bots, grid_size=grid_size, storm_border=0)

    all_rounds: list[dict[str, Any]] = []
    all_eliminations: list[dict[str, Any]] = []
    last_bump_events: list[dict[str, Any]] = []
    spectacle_engine = SpectacleEngine()
    trap_manager = TrapManager()
    for b in bots:
        b._trap_manager = trap_manager
    prev_storm_border = 0
    collected_crystals: set[tuple[int, int]] = set()

    for round_num in range(1, mode.max_rounds + 1):
        if sum(b.alive for b in bots) <= 1:
            break

        storm_border = get_storm_border_for_mode(round_num, mode)
        for b in bots:
            b._current_round = round_num
        round_data, round_elims, last_bump_events = _execute_round(
            bots, round_num, grid_size, storm_border,
            bumps_last_round=last_bump_events, rng=rng,
            trap_manager=trap_manager,
            terrain=terrain, collected_crystals=collected_crystals,
        )
        apply_momentum_phase(bots, round_data, round_num, storm_border, prev_storm_border)
        evolve_events = run_evolve_callbacks(bots, round_num, grid_size, storm_border)
        if evolve_events:
            round_data.setdefault("events", []).extend(evolve_events)
        score_spectacle(spectacle_engine, round_data, bots)
        run_react_callbacks(bots, round_data.get("events", []), grid_size, storm_border, round_num)
        all_rounds.append(round_data)
        all_eliminations.extend(round_elims)
        prev_storm_border = storm_border

        if sum(b.alive for b in bots) <= 1:
            break
    else:
        round_num = mode.max_rounds

    result = _finalize_match(
        bots, players, all_rounds, all_eliminations,
        round_num, match_id, grid_size, profiles_path,
        match_mode=mode.name,
    )
    result["map"] = map_name
    result["terrain_tiles"] = terrain.tiles
    return result
