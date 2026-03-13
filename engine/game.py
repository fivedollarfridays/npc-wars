"""Main match engine for NPC Wars."""

import random
from engine.combat import Bot, resolve_deaths
from engine.grid import calculate_grid_size, spawn_positions, get_storm_border
from engine.match_writer import build_match_data
from engine.rounds import (
    resolve_decisions, resolve_defense, resolve_movement,
    resolve_attacks, apply_storm_damage, apply_energy_and_rest,
    attribute_kills, build_round_record,
)

__all__ = ["MAX_ROUNDS", "run_match"]

MAX_ROUNDS = 200  # Safety limit


def _create_bots(bot_configs, positions):
    """Create Bot instances from configs and spawn positions."""
    bots = []
    for i, config in enumerate(bot_configs):
        x, y = positions[i]
        bots.append(Bot(
            name=config["name"], emoji=config["emoji"],
            bio=config["bio"], author=config.get("author", "unknown"),
            decide_func=config["decide_func"], x=x, y=y,
        ))
    return bots


def _resolve_tiebreaker(bots, round_num, all_eliminations):
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


def _execute_round(bots, round_num, grid_size, storm_border):
    """Execute one round of the match. Returns (round_data, eliminations)."""
    alive_bots = [b for b in bots if b.alive]
    actions, forced_rest = resolve_decisions(alive_bots, bots, round_num, grid_size, storm_border)
    resolve_defense(alive_bots, actions)
    resolve_movement(alive_bots, actions, grid_size)
    round_events = resolve_attacks(alive_bots, actions)
    round_events.extend(apply_storm_damage(alive_bots, grid_size, storm_border))
    apply_energy_and_rest(alive_bots, actions, forced_rest)

    round_elims = resolve_deaths(bots, round_num)
    attribute_kills(round_elims, round_events, bots, round_num)

    for bot in alive_bots:
        if bot.alive:
            bot.rounds_survived = round_num

    round_data = build_round_record(bots, actions, round_num, storm_border, round_events)
    return round_data, round_elims


def run_match(bot_configs: list[dict], match_id: int = 1, seed: int | None = None) -> dict:
    """Run a complete match. Returns match data dict."""
    rng = random.Random(seed)
    grid_size = calculate_grid_size(len(bot_configs))
    positions = spawn_positions(len(bot_configs), grid_size, rng)
    bots = _create_bots(bot_configs, positions)
    players = [{"emoji": b.emoji, "name": b.name, "bio": b.bio, "author": b.author} for b in bots]

    all_rounds = []
    all_eliminations = []

    for round_num in range(1, MAX_ROUNDS + 1):
        if sum(b.alive for b in bots) <= 1:
            break

        round_data, round_elims = _execute_round(bots, round_num, grid_size, get_storm_border(round_num))
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

    return build_match_data(
        match_id=match_id, grid_size=grid_size, players=players,
        rounds=all_rounds, eliminations=all_eliminations,
        winner_emoji=winner_emoji, stats=stats, duration_rounds=round_num,
    )
