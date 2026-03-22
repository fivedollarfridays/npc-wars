"""Main match engine for NPC Wars."""

import random
from pathlib import Path
from typing import Any

from engine.combat import Bot, resolve_deaths, STARTING_ATTACK_POWER, get_round_bonus_attack, tick_damage_bonus
from engine.equipment import EQUIPMENT_DEFAULTS, compute_equipment_bonuses
from engine.momentum import apply_energy_drain, apply_momentum_bonuses, calculate_carryover, determine_leader, get_tier_name
from engine.plague import apply_plague, is_active_action, update_passivity
from engine.scoring import calculate_round_scores
from engine.grid import calculate_grid_size, spawn_positions
from engine.match_modes import MatchMode, get_mode, get_storm_border_for_mode
from engine.match_writer import build_match_data
from engine.discord_integration import notify_match_start, notify_match_end
from engine.callback_runner import run_on_kill_callbacks, run_react_callbacks, run_setup_callbacks
from engine.spectacle import SpectacleEngine
from engine.trap_resolution import resolve_trap_placement, resolve_trap_triggers
from engine.traps import TrapManager
from data.player_profiles import update_profiles_after_match
from engine.rounds import (
    resolve_decisions, resolve_defense, resolve_movement,
    resolve_attacks, resolve_ranged_attacks, resolve_taunt,
    apply_storm_damage, apply_energy_and_rest,
    attribute_kills, build_round_record, build_pos_map,
)

__all__ = ["MAX_ROUNDS", "run_match", "run_match_async"]


async def run_match_async(
    bot_configs: list[dict[str, Any]], match_id: int = 1, seed: int | None = None,
    profiles_path: Path | None = None, human_timeout: float = 2.0,
    match_mode: str = "standard",
) -> dict[str, Any]:
    """Async match loop — delegates to engine.game_async."""
    from engine.game_async import run_match_async as _impl
    return await _impl(
        bot_configs, match_id=match_id, seed=seed,
        profiles_path=profiles_path, human_timeout=human_timeout,
        match_mode=match_mode,
    )

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
            stat_allocation=config.get("stat_allocation"),
            glyph=config.get("glyph"),
        )
        for fld in _PROGRESSION_FIELDS:
            if fld in config:
                setattr(bot_obj, fld, config[fld])
        if "human_adapter" in config:
            bot_obj.human_adapter = config["human_adapter"]
        # Equipment: load selections and apply bonuses
        equipment = config.get("equipment", dict(EQUIPMENT_DEFAULTS))
        bot_obj.equipment = equipment
        bonuses = compute_equipment_bonuses(equipment)
        bot_obj.equipment_bonuses = bonuses
        bot_obj.hp += bonuses.max_hp
        bot_obj.energy += bonuses.max_energy
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


def _apply_round_scores(
    bots: list[Bot], round_data: dict[str, Any],
    round_num: int, storm_border: int, prev_storm_border: int,
    leader_emoji: str | None = None,
) -> None:
    """Calculate and apply per-round scores to bots, attach to round_data."""
    bot_dicts = [
        {"emoji": b.emoji, "alive": b.alive, "hp": b.hp,
         "max_hp": b.derived.max_hp}
        for b in bots
    ]
    scores, score_events = calculate_round_scores(
        bot_dicts, round_data.get("events", []),
        round_num, storm_border, prev_storm_border,
        leader_emoji=leader_emoji,
    )
    for bot in bots:
        bot.score += scores.get(bot.emoji, 0)
    round_data["score_events"] = [
        {"emoji": e.emoji, "source": e.source, "points": e.points}
        for e in score_events
    ]
    # Append leader_bounty events to round events for feed display
    events = round_data.get("events", [])
    kill_victims_by_attacker = {
        e.get("attacker"): e.get("victim")
        for e in events if e.get("type") == "kill"
    }
    for e in score_events:
        if e.source == "leader_bounty" and e.emoji in kill_victims_by_attacker:
            events.append({
                "type": "leader_bounty",
                "killer": e.emoji,
                "victim": kill_victims_by_attacker[e.emoji],
                "bonus": e.points,
            })


def _apply_plague_phase(
    alive_bots: list[Bot], actions: dict[str, tuple[str, ...]],
) -> list[dict[str, Any]]:
    """Track passivity and apply plague penalties for each alive bot."""
    plague_events: list[dict[str, Any]] = []
    for bot in alive_bots:
        if not bot.alive:
            continue
        action = actions.get(bot.emoji, ("rest",))
        enemy_dicts = [{"x": e.x, "y": e.y} for e in alive_bots if e.emoji != bot.emoji and e.alive]
        active = is_active_action(action, bot, enemy_dicts)
        update_passivity(bot, is_active=active)
        plague_events.extend(apply_plague(bot))
    return plague_events


def _resolve_combat_phases(
    alive_bots: list[Bot], bots: list[Bot], actions: dict[str, tuple[str, ...]],
    forced_rest: set[str], override_events: list[dict[str, Any]],
    round_num: int, grid_size: int, storm_border: int,
    rng: random.Random | None = None,
    trap_manager: TrapManager | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Phases 2-7: defense, movement, traps, attacks, storm, energy, deaths."""
    defend_events = resolve_defense(alive_bots, actions)
    bump_events = resolve_movement(
        alive_bots, actions, grid_size, all_bots=bots, storm_border=storm_border,
    )

    # Trap phases: triggers after movement, then placement
    trap_events: list[dict[str, Any]] = []
    if trap_manager is not None:
        trap_events.extend(resolve_trap_triggers(alive_bots, trap_manager, round_num))
        trap_events.extend(resolve_trap_placement(alive_bots, actions, trap_manager, round_num, grid_size))

    taunt_events = resolve_taunt(alive_bots, actions)
    pos_map = build_pos_map(alive_bots)
    round_events = override_events + defend_events + bump_events + trap_events
    round_events.extend(resolve_attacks(alive_bots, actions, pos_map, rng=rng))
    round_events.extend(taunt_events)
    round_events.extend(resolve_ranged_attacks(alive_bots, actions, pos_map, rng=rng))
    round_events.extend(apply_storm_damage(alive_bots, grid_size, storm_border))
    apply_energy_and_rest(alive_bots, actions, forced_rest)

    round_events.extend(_apply_plague_phase(alive_bots, actions))

    round_elims = resolve_deaths(bots, round_num)
    attribute_kills(round_elims, round_events, bots, round_num)
    run_on_kill_callbacks(bots, round_elims, round_num, grid_size, storm_border)
    tick_damage_bonus(alive_bots)

    # Trap cleanup: expire old traps, remove dead bot traps
    if trap_manager is not None:
        trap_manager.expire_traps(round_num)
        for elim in round_elims:
            trap_manager.remove_bot_traps(elim["emoji"])

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
    players = [{"emoji": b.emoji, "name": b.name, "bio": b.bio, "author": b.author, "glyph": b.glyph} for b in bots]
    return bots, players, grid_size, rng


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
                        "momentum_name": get_tier_name(b.score)}
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


def _apply_momentum_phase(
    bots: list[Bot], round_data: dict[str, Any],
    round_num: int, storm_border: int, prev_storm_border: int,
) -> None:
    """Determine leader, apply scores/momentum/drain for one round."""
    leader = determine_leader([b for b in bots if b.alive])
    leader_emoji = leader.emoji if leader is not None else None
    _apply_round_scores(
        bots, round_data, round_num, storm_border, prev_storm_border,
        leader_emoji=leader_emoji,
    )
    for b in bots:
        b.is_leader = (leader is not None and b is leader)
    for b in bots:
        if b.alive:
            apply_momentum_bonuses(b, is_leader=b.is_leader)
    for b in bots:
        if b.alive:
            drain = apply_energy_drain(b)
            if drain > 0:
                round_data.setdefault("events", []).append({
                    "type": "momentum_drain",
                    "emoji": b.emoji,
                    "energy_cost": drain,
                })


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
    rng: random.Random | None = None,
    trap_manager: TrapManager | None = None,
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
        round_num, grid_size, storm_border, rng=rng,
        trap_manager=trap_manager,
    )


def run_match(
    bot_configs: list[dict[str, Any]], match_id: int = 1, seed: int | None = None,
    profiles_path: Path | None = None, match_mode: str = "standard",
) -> dict[str, Any]:
    """Run a complete match. Returns match data dict."""
    mode = get_mode(match_mode)
    bots, players, grid_size, rng = _prepare_match(bot_configs, seed, mode=mode)
    notify_match_start(match_id=match_id, players=players, seed=seed)

    run_setup_callbacks(bots, grid_size=grid_size, storm_border=0)

    all_rounds: list[dict[str, Any]] = []
    all_eliminations: list[dict[str, Any]] = []
    last_bump_events: list[dict[str, Any]] = []
    spectacle_engine = SpectacleEngine()
    trap_manager = TrapManager()
    for b in bots:
        b._trap_manager = trap_manager
    prev_storm_border = 0

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
        )
        _apply_momentum_phase(bots, round_data, round_num, storm_border, prev_storm_border)
        _score_spectacle(spectacle_engine, round_data, bots)
        run_react_callbacks(bots, round_data.get("events", []), grid_size, storm_border, round_num)
        all_rounds.append(round_data)
        all_eliminations.extend(round_elims)
        prev_storm_border = storm_border

        if sum(b.alive for b in bots) <= 1:
            break
    else:
        round_num = mode.max_rounds

    return _finalize_match(
        bots, players, all_rounds, all_eliminations,
        round_num, match_id, grid_size, profiles_path,
        match_mode=mode.name,
    )
