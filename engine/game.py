"""Main match engine for NPC Wars."""

import random
from pathlib import Path
from typing import Any

from engine.combat import Bot, resolve_deaths, STARTING_ATTACK_POWER, get_round_bonus_attack
from engine.grid import calculate_grid_size, spawn_positions, get_storm_border
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

__all__ = ["MAX_ROUNDS", "run_match"]

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


def _execute_round(
    bots: list[Bot], round_num: int, grid_size: int, storm_border: int,
    bumps_last_round: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Execute one round of the match. Returns (round_data, eliminations, bump_events)."""
    alive_bots = [b for b in bots if b.alive]

    # Apply round-based damage scaling
    bonus = get_round_bonus_attack(round_num)
    for bot in alive_bots:
        bot.attack_power = STARTING_ATTACK_POWER + bonus

    actions, forced_rest = resolve_decisions(alive_bots, bots, round_num, grid_size, storm_border,
                                              bumps_last_round=bumps_last_round)
    resolve_defense(alive_bots, actions)
    bump_events = resolve_movement(
        alive_bots, actions, grid_size, all_bots=bots, storm_border=storm_border,
    )
    taunt_events = resolve_taunt(alive_bots, actions)
    pos_map = build_pos_map(alive_bots)
    round_events = bump_events + resolve_attacks(alive_bots, actions, pos_map)
    round_events.extend(taunt_events)
    round_events.extend(resolve_ranged_attacks(alive_bots, actions, pos_map))
    round_events.extend(apply_storm_damage(alive_bots, grid_size, storm_border))
    apply_energy_and_rest(alive_bots, actions, forced_rest)

    round_elims = resolve_deaths(bots, round_num)
    attribute_kills(round_elims, round_events, bots, round_num)

    for bot in alive_bots:
        if bot.alive:
            bot.rounds_survived = round_num

    round_data = build_round_record(bots, actions, round_num, storm_border, round_events)
    return round_data, round_elims, bump_events


def run_match(
    bot_configs: list[dict[str, Any]], match_id: int = 1,
    seed: int | None = None, profiles_path: Path | None = None,
) -> dict[str, Any]:
    """Run a complete match. Returns match data dict."""
    rng = random.Random(seed)
    grid_size = calculate_grid_size(len(bot_configs))
    positions = spawn_positions(len(bot_configs), grid_size, rng)
    bots = _create_bots(bot_configs, positions)
    players = [{"emoji": b.emoji, "name": b.name, "bio": b.bio, "author": b.author} for b in bots]

    notify_match_start(match_id=match_id, players=players, seed=seed)

    all_rounds: list[dict[str, Any]] = []
    all_eliminations: list[dict[str, Any]] = []
    last_bump_events: list[dict[str, Any]] = []
    spectacle_engine = SpectacleEngine()

    for round_num in range(1, MAX_ROUNDS + 1):
        if sum(b.alive for b in bots) <= 1:
            break

        round_data, round_elims, last_bump_events = _execute_round(
            bots, round_num, grid_size, get_storm_border(round_num),
            bumps_last_round=last_bump_events,
        )
        bot_states = [{"emoji": b.emoji, "hp": b.hp, "alive": b.alive} for b in bots]
        sd = spectacle_engine.score_round(round_data.get("events", []), bot_states)
        round_data["spectacle"] = {
            "drama_score": sd.drama_score,
            "tier": sd.tier,
            "triggers": sd.triggers,
            "effects": sd.effects,
        }
        all_rounds.append(round_data)
        all_eliminations.extend(round_elims)

        if sum(b.alive for b in bots) <= 1:
            break
    else:
        round_num = MAX_ROUNDS

    winner_emoji = _resolve_tiebreaker(bots, round_num, all_eliminations)
    stats = {b.emoji: {"kills": b.kills, "damage_dealt": b.damage_dealt,
                        "damage_taken": b.damage_taken, "rounds_survived": b.rounds_survived}
             for b in bots}

    match_data = build_match_data(
        match_id=match_id, grid_size=grid_size, players=players,
        rounds=all_rounds, eliminations=all_eliminations,
        winner_emoji=winner_emoji, stats=stats, duration_rounds=round_num,
    )
    notify_match_end(match_data)

    if profiles_path is not None:
        update_profiles_after_match(profiles_path, players, winner_emoji)

    return match_data
