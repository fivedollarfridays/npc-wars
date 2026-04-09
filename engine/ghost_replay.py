"""Ghost replay: fork a match at any round and re-simulate an alternate timeline."""

import copy
import random
from typing import Any

from engine.combat import Bot, STARTING_ATTACK_POWER, get_round_bonus_attack
from engine.match_modes import get_mode, get_storm_border_for_mode
from engine.match_phases import resolve_combat_phases, apply_momentum_phase
from engine.traps import TrapManager

__all__ = ["ghost_replay"]


def ghost_replay(
    match_data: dict[str, Any],
    round_num: int,
    bot_emoji: str,
    alt_action: str,
    seed: int,
) -> dict[str, Any]:
    """Fork match at *round_num*, substitute *bot_emoji*'s action, re-simulate.

    Returns a ghost match dict with ``divergence_point`` marked on the fork
    round and ``ghost: True`` at top level.  Original *match_data* is never
    modified.
    """
    rounds = match_data["rounds"]
    if round_num < 1 or round_num > len(rounds):
        raise ValueError(f"round_num {round_num} out of range 1..{len(rounds)}")

    ghost_rounds: list[dict[str, Any]] = copy.deepcopy(rounds[: round_num - 1])
    bots = _reconstruct_bots(match_data, round_num)
    mode = get_mode(match_data.get("match_mode", "standard"))
    prev_storm = rounds[round_num - 2]["storm_border"] if round_num > 1 else 0

    _simulate_ghost(
        bots, rounds, ghost_rounds, match_data["grid_size"], mode,
        random.Random(seed), round_num, bot_emoji, alt_action, prev_storm,
    )
    return _build_ghost_result(match_data, ghost_rounds, bots, round_num)


def _simulate_ghost(
    bots: list[Bot],
    original_rounds: list[dict[str, Any]],
    ghost_rounds: list[dict[str, Any]],
    grid_size: int,
    mode: Any,
    rng: random.Random,
    fork_round: int,
    bot_emoji: str,
    alt_action: str,
    prev_storm: int,
) -> None:
    """Run the ghost simulation loop, appending rounds to *ghost_rounds*."""
    trap_manager = TrapManager()
    for r in range(fork_round, mode.max_rounds + 1):
        alive = [b for b in bots if b.alive]
        if len(alive) <= 1:
            break

        storm_border = get_storm_border_for_mode(r, mode)
        actions = _actions_for_round(
            original_rounds, r, fork_round, bot_emoji, alt_action, alive,
        )
        bonus = get_round_bonus_attack(r)
        for b in alive:
            b.attack_power = STARTING_ATTACK_POWER + bonus

        rd, _elims, _bumps = resolve_combat_phases(
            alive, bots, actions, set(), [],
            r, grid_size, storm_border, rng=rng, trap_manager=trap_manager,
        )
        apply_momentum_phase(bots, rd, r, storm_border, prev_storm)
        if r == fork_round:
            rd["divergence_point"] = True
        ghost_rounds.append(rd)
        prev_storm = storm_border
        if sum(1 for b in bots if b.alive) <= 1:
            break


def _reconstruct_bots(
    match_data: dict[str, Any], round_num: int,
) -> list[Bot]:
    """Create Bot objects from match state just before *round_num*."""
    if round_num > 1:
        positions = match_data["rounds"][round_num - 2]["positions"]
    else:
        positions = match_data["rounds"][0]["positions"]

    bots: list[Bot] = []
    for pos in positions:
        bot = Bot(
            name=pos["emoji"], emoji=pos["emoji"], bio="", author="ghost",
            decide_func=lambda _s: ("rest",), x=pos["x"], y=pos["y"],
            glyph=pos.get("glyph", pos["emoji"]),
        )
        if round_num > 1:
            bot.hp = float(pos["hp"])
            bot.energy = pos["energy"]
            bot.alive = pos["alive"]
            bot.score = pos.get("score", 0)
            bot.momentum_tier = pos.get("momentum_tier", 0)
            bot.is_leader = pos.get("is_leader", False)
        bots.append(bot)
    return bots


def _parse_action(action_str: str) -> tuple[str, ...]:
    """Parse ``'attack north'`` into ``('attack', 'north')``."""
    return tuple(action_str.strip().split())


def _actions_for_round(
    rounds: list[dict[str, Any]],
    r: int,
    fork_round: int,
    bot_emoji: str,
    alt_action: str,
    alive: list[Bot],
) -> dict[str, tuple[str, ...]]:
    """Build the actions map for round *r* of the ghost timeline."""
    actions: dict[str, tuple[str, ...]] = {}
    alive_emojis = {b.emoji for b in alive}

    if r <= len(rounds):
        for pos in rounds[r - 1]["positions"]:
            if pos["emoji"] in alive_emojis:
                actions[pos["emoji"]] = _parse_action(pos["action"])

    for b in alive:
        if b.emoji not in actions:
            actions[b.emoji] = ("rest",)

    if r == fork_round:
        actions[bot_emoji] = _parse_action(alt_action)

    return actions


def _determine_winner(bots: list[Bot]) -> str:
    alive = [b for b in bots if b.alive]
    if len(alive) == 1:
        return alive[0].emoji
    if alive:
        alive.sort(key=lambda b: (b.hp, b.energy), reverse=True)
        return alive[0].emoji
    return "none"


def _build_ghost_result(
    original: dict[str, Any],
    ghost_rounds: list[dict[str, Any]],
    bots: list[Bot],
    divergence_round: int,
) -> dict[str, Any]:
    """Assemble the ghost match JSON from simulation results."""
    result: dict[str, Any] = {}
    for key in ("match_id", "date", "grid_size", "players", "match_mode", "map"):
        if key in original:
            result[key] = copy.deepcopy(original[key])

    result["rounds"] = ghost_rounds
    result["winner"] = _determine_winner(bots)
    result["original_winner"] = original.get("winner")
    result["duration_rounds"] = len(ghost_rounds)
    result["ghost"] = True
    result["divergence_round"] = divergence_round
    result["stats"] = {
        b.emoji: {
            "kills": b.kills, "damage_dealt": b.damage_dealt,
            "damage_taken": b.damage_taken, "rounds_survived": b.rounds_survived,
        }
        for b in bots
    }
    result["eliminations"] = _collect_eliminations(ghost_rounds)
    return result


def _collect_eliminations(rounds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    elims: list[dict[str, Any]] = []
    for rd in rounds:
        for evt in rd.get("events", []):
            if evt.get("type") == "kill":
                elims.append({
                    "emoji": evt["victim"], "round": rd["round"],
                    "killed_by": evt["attacker"],
                    "cause": "storm" if evt["attacker"] == "storm" else "combat",
                })
    return elims
