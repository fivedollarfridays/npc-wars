"""Terrain balance simulation -- run matches across all 5 maps."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.game import run_match  # noqa: E402
from engine.loader import load_bots  # noqa: E402
from engine.terrain import MAP_NAMES  # noqa: E402


def run_simulation(
    n_matches: int = 200, seed_base: int = 9000,
) -> dict[str, dict[str, Any]]:
    """Run *n_matches* across all maps (evenly split) and collect stats."""
    bots_dir = str(Path(__file__).resolve().parent.parent / "bots")
    all_bots = load_bots(bots_dir)
    if len(all_bots) < 4:
        print(f"Need at least 4 bots, found {len(all_bots)}")
        sys.exit(1)

    _unlock_actions(all_bots)

    names = [b["name"] for b in all_bots]
    maps = list(MAP_NAMES)
    per_map = n_matches // len(maps)

    # Per-bot-per-map tracking
    wins: dict[str, dict[str, int]] = {n: {m: 0 for m in maps} for n in names}
    total: dict[str, dict[str, int]] = {n: {m: 0 for m in maps} for n in names}

    rng = random.Random(seed_base)

    match_num = 0
    for map_name in maps:
        for _ in range(per_map):
            k = rng.randint(4, min(6, len(all_bots)))
            chosen_indices = rng.sample(range(len(all_bots)), k)
            seed = seed_base + match_num
            configs = [all_bots[i] for i in chosen_indices]

            result = run_match(
                configs, match_id=match_num, seed=seed, map_name=map_name,
            )
            winner_emoji = result.get("winner", "none")

            for i in chosen_indices:
                total[names[i]][map_name] += 1
                if winner_emoji == all_bots[i]["emoji"]:
                    wins[names[i]][map_name] += 1

            match_num += 1

    return _build_results(names, maps, wins, total)


def _unlock_actions(all_bots: list[dict[str, Any]]) -> None:
    """Give all bots the full set of unlocked actions."""
    full_actions = sorted({
        "move", "attack", "rest", "defend",
        "ranged_attack", "dash", "taunt",
        "trap", "use_ability", "use_tactical",
    })
    for b in all_bots:
        b["unlocked_actions"] = list(full_actions)


def _build_results(
    names: list[str],
    maps: list[str],
    wins: dict[str, dict[str, int]],
    total: dict[str, dict[str, int]],
) -> dict[str, dict[str, Any]]:
    """Build the results dict with per-bot, per-map stats."""
    results: dict[str, dict[str, Any]] = {}
    for name in names:
        per_map: dict[str, dict[str, Any]] = {}
        total_wins = 0
        total_games = 0
        for m in maps:
            t = total[name][m]
            w = wins[name][m]
            rate = (w / t * 100) if t > 0 else 0.0
            per_map[m] = {"wins": w, "total": t, "win_rate": round(rate, 1)}
            total_wins += w
            total_games += t
        overall_rate = (total_wins / total_games * 100) if total_games > 0 else 0.0
        results[name] = {
            "overall_wins": total_wins,
            "overall_total": total_games,
            "overall_win_rate": round(overall_rate, 1),
            "per_map": per_map,
        }
    return results


def main() -> None:
    n = 200
    print(f"Running terrain balance simulation ({n} matches, {len(MAP_NAMES)} maps)...")
    results = run_simulation(n_matches=n)

    print(f"\n{'Bot':<15} {'Overall':>8}", end="")
    for m in MAP_NAMES:
        print(f" {m:>10}", end="")
    print()
    print("-" * (25 + 11 * len(MAP_NAMES)))

    for name, data in sorted(
        results.items(), key=lambda x: x[1]["overall_win_rate"], reverse=True,
    ):
        print(f"{name:<15} {data['overall_win_rate']:>7.1f}%", end="")
        for m in MAP_NAMES:
            rate = data["per_map"][m]["win_rate"]
            print(f" {rate:>9.1f}%", end="")
        print()

    output = Path("tools/terrain_balance_results.json")
    output.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {output}")


if __name__ == "__main__":
    main()
