"""Unified Phase 2 balance simulation.

Runs 1000 matches (200 per map) with random 4-6 bot subsets.
Tracks per-bot, per-archetype, per-map, and per-weapon statistics.
Saves results to tools/phase2_balance_results.json.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.archetype import classify_archetype  # noqa: E402
from engine.game import run_match  # noqa: E402
from engine.loader import load_bots  # noqa: E402
from engine.terrain import MAP_NAMES  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BOTS_DIR = str(PROJECT_ROOT / "bots")
OUTPUT_PATH = Path(__file__).resolve().parent / "phase2_balance_results.json"

N_MATCHES = 1000
SEED_BASE = 20000

_FULL_ACTIONS = sorted({
    "move", "attack", "rest", "defend",
    "ranged_attack", "dash", "taunt",
    "trap", "use_ability", "use_tactical",
})


def _unlock_actions(all_bots: list[dict[str, Any]]) -> None:
    """Give all bots the full set of unlocked actions."""
    for b in all_bots:
        b["unlocked_actions"] = list(_FULL_ACTIONS)


def _init_trackers(
    all_bots: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, int]], dict[str, dict[str, int]], dict[str, dict[str, Any]], dict[str, int]]:
    """Initialize all tracking dicts."""
    names = [b["name"] for b in all_bots]

    bot_stats: dict[str, dict[str, int]] = {
        n: {"wins": 0, "total_matches": 0} for n in names
    }

    archetype_map: dict[str, str] = {}
    for b in all_bots:
        archetype_map[b["name"]] = classify_archetype(b["stat_allocation"])

    arch_names = set(archetype_map.values())
    arch_stats: dict[str, dict[str, int]] = {
        a: {"wins": 0, "total": 0} for a in arch_names
    }

    map_stats: dict[str, dict[str, Any]] = {
        m: {"matches": 0, "total_rounds": 0} for m in MAP_NAMES
    }

    weapon_wins: dict[str, int] = {}

    return bot_stats, arch_stats, map_stats, weapon_wins


def _record_match(
    result: dict[str, Any],
    chosen: list[dict[str, Any]],
    map_name: str,
    bot_stats: dict[str, dict[str, int]],
    arch_stats: dict[str, dict[str, int]],
    map_stats: dict[str, dict[str, Any]],
    weapon_wins: dict[str, int],
    archetype_map: dict[str, str],
) -> None:
    """Record a single match result into all trackers."""
    winner_emoji = result.get("winner", "none")
    n_rounds = len(result.get("rounds", []))

    map_stats[map_name]["matches"] += 1
    map_stats[map_name]["total_rounds"] += n_rounds

    for bot in chosen:
        name = bot["name"]
        bot_stats[name]["total_matches"] += 1
        arch = archetype_map[name]
        arch_stats[arch]["total"] += 1

        if winner_emoji == bot["emoji"]:
            bot_stats[name]["wins"] += 1
            arch_stats[arch]["wins"] += 1

            weapon = bot.get("equipment", {}).get("weapon", "fists")
            weapon_wins[weapon] = weapon_wins.get(weapon, 0) + 1


def _build_archetype_map(all_bots: list[dict[str, Any]]) -> dict[str, str]:
    """Build name -> archetype mapping."""
    return {b["name"]: classify_archetype(b["stat_allocation"]) for b in all_bots}


def run_simulation(
    n_matches: int = N_MATCHES, seed_base: int = SEED_BASE,
) -> dict[str, Any]:
    """Run the full Phase 2 balance simulation."""
    all_bots = load_bots(BOTS_DIR)
    if len(all_bots) < 4:
        print(f"Need at least 4 bots, found {len(all_bots)}")
        sys.exit(1)

    _unlock_actions(all_bots)
    archetype_map = _build_archetype_map(all_bots)
    bot_stats, arch_stats, map_stats, weapon_wins = _init_trackers(all_bots)

    maps = list(MAP_NAMES)
    per_map = n_matches // len(maps)
    rng = random.Random(seed_base)

    match_num = 0
    for map_name in maps:
        for _ in range(per_map):
            k = rng.randint(4, min(6, len(all_bots)))
            chosen_indices = rng.sample(range(len(all_bots)), k)
            chosen = [all_bots[i] for i in chosen_indices]
            seed = seed_base + match_num

            result = run_match(
                chosen, match_id=match_num, seed=seed, map_name=map_name,
            )
            _record_match(
                result, chosen, map_name,
                bot_stats, arch_stats, map_stats, weapon_wins, archetype_map,
            )

            match_num += 1
            if match_num % 100 == 0:
                print(f"  Progress: {match_num}/{n_matches} matches")

    return _format_results(bot_stats, arch_stats, map_stats, weapon_wins, match_num)


def _format_results(
    bot_stats: dict[str, dict[str, int]],
    arch_stats: dict[str, dict[str, int]],
    map_stats: dict[str, dict[str, Any]],
    weapon_wins: dict[str, int],
    total_matches: int,
) -> dict[str, Any]:
    """Format all tracking dicts into the final results structure."""
    per_bot: dict[str, dict[str, Any]] = {}
    for name, s in bot_stats.items():
        t = s["total_matches"]
        w = s["wins"]
        per_bot[name] = {
            "wins": w,
            "total_matches": t,
            "win_rate": round((w / t * 100) if t > 0 else 0.0, 1),
        }

    per_arch: dict[str, dict[str, Any]] = {}
    for name, s in arch_stats.items():
        t = s["total"]
        w = s["wins"]
        per_arch[name] = {
            "wins": w,
            "total": t,
            "win_rate": round((w / t * 100) if t > 0 else 0.0, 1),
        }

    per_map: dict[str, dict[str, Any]] = {}
    for name, s in map_stats.items():
        m = s["matches"]
        per_map[name] = {
            "matches": m,
            "avg_duration": round(s["total_rounds"] / m, 1) if m > 0 else 0,
        }

    return {
        "per_bot": per_bot,
        "per_archetype": per_arch,
        "per_map": per_map,
        "per_weapon": weapon_wins,
        "meta": {"total_matches": total_matches},
    }


def _print_summary(results: dict[str, Any]) -> None:
    """Print a human-readable summary."""
    print(f"\n{'='*60}")
    print("PHASE 2 UNIFIED BALANCE RESULTS")
    print(f"{'='*60}")
    print(f"Total matches: {results['meta']['total_matches']}")

    print("\n--- Per Bot ---")
    print(f"{'Bot':<20} {'Wins':>6} {'Total':>7} {'Win Rate':>9}")
    print("-" * 45)
    for name, s in sorted(
        results["per_bot"].items(), key=lambda x: x[1]["win_rate"], reverse=True,
    ):
        print(f"{name:<20} {s['wins']:>6} {s['total_matches']:>7} {s['win_rate']:>8.1f}%")

    print("\n--- Per Archetype ---")
    print(f"{'Archetype':<15} {'Wins':>6} {'Total':>7} {'Win Rate':>9}")
    print("-" * 40)
    for name, s in sorted(
        results["per_archetype"].items(), key=lambda x: x[1]["win_rate"], reverse=True,
    ):
        print(f"{name:<15} {s['wins']:>6} {s['total']:>7} {s['win_rate']:>8.1f}%")

    print("\n--- Per Map ---")
    print(f"{'Map':<15} {'Matches':>8} {'Avg Rounds':>11}")
    print("-" * 36)
    for name, s in results["per_map"].items():
        print(f"{name:<15} {s['matches']:>8} {s['avg_duration']:>10.1f}")

    print("\n--- Weapon Wins ---")
    for w, c in sorted(results["per_weapon"].items(), key=lambda x: -x[1]):
        print(f"  {w}: {c}")

    # Balance assessment
    max_bot_wr = max(s["win_rate"] for s in results["per_bot"].values())
    max_arch_wr = max(s["win_rate"] for s in results["per_archetype"].values())
    print(f"\nMax bot win rate: {max_bot_wr}% (target: <=60%)")
    print(f"Max archetype win rate: {max_arch_wr}% (target: <=60%)")

    if max_bot_wr > 60:
        print("WARNING: A bot exceeds 60% win rate")
    elif max_arch_wr > 60:
        print("WARNING: An archetype exceeds 60% win rate")
    else:
        print("OK: Phase 2 balance targets met")


def main() -> None:
    """Run the simulation and save results."""
    print(f"Running Phase 2 unified balance simulation ({N_MATCHES} matches)...")
    print(f"Maps: {', '.join(MAP_NAMES)}")
    print(f"Matches per map: {N_MATCHES // len(MAP_NAMES)}")
    print()

    results = run_simulation()
    _print_summary(results)

    OUTPUT_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
