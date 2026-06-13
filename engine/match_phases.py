"""Per-round match phase helpers: combat, plague, momentum, scoring, spectacle."""

import random
from typing import Any

from engine.combat import Bot, resolve_deaths, tick_damage_bonus
from engine.event_meta import TICK_MOMENTUM, position
from engine.tactical import resolve_tactical_activation, tick_tactical_effects, tick_tactical_cooldowns
from engine.momentum import apply_energy_drain, apply_momentum_bonuses, determine_leader
from engine.plague import apply_plague, is_active_action, update_passivity
from engine.scoring import calculate_round_scores
from engine.abilities import resolve_ability_phase, tick_ability_cooldowns, tick_ability_effects
from engine.callback_runner import run_on_kill_callbacks
from engine.spectacle import SpectacleEngine
from engine.trap_resolution import resolve_trap_placement, resolve_trap_triggers
from engine.traps import TrapManager
from engine.rounds import (
    resolve_defense, resolve_movement,
    resolve_attacks, resolve_ranged_attacks, resolve_taunt,
    apply_storm_damage, apply_energy_and_rest,
    attribute_kills, build_round_record, build_pos_map,
)

__all__ = [
    "apply_plague_phase",
    "apply_round_scores",
    "resolve_combat_phases",
    "apply_momentum_phase",
    "score_spectacle",
]


def apply_round_scores(
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


def apply_plague_phase(
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


def _resolve_tactical_phase(
    alive_bots: list[Bot], actions: dict[str, tuple[str, ...]], round_num: int,
) -> list[dict[str, Any]]:
    """Tactical activation phase (before combat): resolve use_tactical actions."""
    tactical_events: list[dict[str, Any]] = []
    for bot in alive_bots:
        action = actions.get(bot.emoji)
        if action and action[0] == "use_tactical":
            direction = action[1] if len(action) > 1 else None
            tactical_events.extend(
                resolve_tactical_activation(bot, round_num, direction=direction)
            )
    return tactical_events


def _resolve_trap_phase(
    alive_bots: list[Bot], actions: dict[str, tuple[str, ...]],
    trap_manager: TrapManager | None, round_num: int, grid_size: int,
) -> list[dict[str, Any]]:
    """Trap phases: triggers after movement, then placement."""
    trap_events: list[dict[str, Any]] = []
    if trap_manager is not None:
        trap_events.extend(resolve_trap_triggers(alive_bots, trap_manager, round_num))
        trap_events.extend(
            resolve_trap_placement(alive_bots, actions, trap_manager, round_num, grid_size)
        )
    return trap_events


def _cleanup_traps(
    trap_manager: TrapManager | None, round_elims: list[dict[str, Any]], round_num: int,
) -> None:
    """Expire old traps and remove traps owned by eliminated bots."""
    if trap_manager is None:
        return
    trap_manager.expire_traps(round_num)
    for elim in round_elims:
        trap_manager.remove_bot_traps(elim["emoji"])


def _tick_end_of_round_effects(alive_bots: list[Bot]) -> None:
    """Tick damage-bonus, tactical, and ability timers at end of round."""
    tick_damage_bonus(alive_bots)
    tick_tactical_effects(alive_bots)
    tick_tactical_cooldowns(alive_bots)
    tick_ability_effects(alive_bots)
    tick_ability_cooldowns(alive_bots)


def resolve_combat_phases(
    alive_bots: list[Bot], bots: list[Bot], actions: dict[str, tuple[str, ...]],
    forced_rest: set[str], override_events: list[dict[str, Any]],
    round_num: int, grid_size: int, storm_border: int,
    rng: random.Random | None = None,
    trap_manager: TrapManager | None = None,
    terrain: Any | None = None,
    collected_crystals: set[tuple[int, int]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Phases 2-7: defense, movement, traps, attacks, storm, energy, deaths."""
    tactical_events = _resolve_tactical_phase(alive_bots, actions, round_num)

    # Ability activation phase (before combat)
    ability_events = resolve_ability_phase(alive_bots, bots, actions, round_num)

    defend_events = resolve_defense(alive_bots, actions)
    bump_events = resolve_movement(
        alive_bots, actions, grid_size, all_bots=bots, storm_border=storm_border,
        terrain=terrain, collected_crystals=collected_crystals,
    )

    trap_events = _resolve_trap_phase(
        alive_bots, actions, trap_manager, round_num, grid_size,
    )

    taunt_events = resolve_taunt(alive_bots, actions)
    pos_map = build_pos_map(alive_bots)
    round_events = override_events + tactical_events + ability_events + defend_events + bump_events + trap_events
    round_events.extend(resolve_attacks(alive_bots, actions, pos_map, rng=rng))
    round_events.extend(taunt_events)
    round_events.extend(resolve_ranged_attacks(alive_bots, actions, pos_map, rng=rng))
    round_events.extend(apply_storm_damage(alive_bots, grid_size, storm_border))
    apply_energy_and_rest(alive_bots, actions, forced_rest, terrain, grid_size, storm_border)

    round_events.extend(apply_plague_phase(alive_bots, actions))

    round_elims = resolve_deaths(bots, round_num)
    attribute_kills(round_elims, round_events, bots, round_num)
    run_on_kill_callbacks(bots, round_elims, round_num, grid_size, storm_border)
    _tick_end_of_round_effects(alive_bots)

    _cleanup_traps(trap_manager, round_elims, round_num)

    for bot in alive_bots:
        if bot.alive:
            bot.rounds_survived = round_num

    round_data = build_round_record(bots, actions, round_num, storm_border, round_events)
    return round_data, round_elims, bump_events


def apply_momentum_phase(
    bots: list[Bot], round_data: dict[str, Any],
    round_num: int, storm_border: int, prev_storm_border: int,
) -> None:
    """Determine leader, apply scores/momentum/drain for one round."""
    leader = determine_leader([b for b in bots if b.alive])
    leader_emoji = leader.emoji if leader is not None else None
    apply_round_scores(
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
                    "tick_in_round": TICK_MOMENTUM,
                    "position": position(b),
                })


def score_spectacle(
    spectacle_engine: SpectacleEngine, round_data: dict[str, Any], bots: list[Bot],
) -> None:
    """Score drama for a round and attach spectacle data."""
    bot_states = [{"emoji": b.emoji, "hp": b.hp, "alive": b.alive} for b in bots]
    sd = spectacle_engine.score_round(round_data.get("events", []), bot_states)
    round_data["spectacle"] = {
        "drama_score": sd.drama_score, "tier": sd.tier,
        "triggers": sd.triggers, "effects": sd.effects,
    }
