"""Balance simulation -- archetype round-robin comparison."""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.game import run_match  # noqa: E402
from engine.stats import StatAllocation  # noqa: E402

ARCHETYPES: dict[str, StatAllocation] = {
    "Balanced": StatAllocation(25, 25, 25, 25),
    "Glass Cannon": StatAllocation(50, 15, 15, 20),
    "Tank": StatAllocation(15, 15, 50, 20),
    "Assassin": StatAllocation(20, 50, 15, 15),
    "Mage": StatAllocation(15, 15, 20, 50),
    "Bruiser": StatAllocation(35, 15, 35, 15),
    "Duelist": StatAllocation(25, 35, 15, 25),
}

EMOJIS = ["\U0001f534", "\U0001f535", "\U0001f7e2", "\U0001f7e1",
          "\U0001f7e3", "\U0001f7e0", "\u26aa"]


def _simple_decide(state: dict[str, Any]) -> tuple[str, ...]:
    """Simple bot AI for balance testing -- chase closest, attack adjacent, rest if low."""
    me = state["me"]
    enemies = state["enemies"]
    if not enemies:
        return ("rest",)
    if me["energy"] < 10:
        return ("rest",)
    closest = min(enemies, key=lambda e: abs(e["x"] - me["x"]) + abs(e["y"] - me["y"]))
    dx = closest["x"] - me["x"]
    dy = closest["y"] - me["y"]
    dist = abs(dx) + abs(dy)
    if dist == 1:
        if abs(dx) > abs(dy):
            direction = "east" if dx > 0 else "west"
        else:
            direction = "south" if dy > 0 else "north"
        return ("attack", direction)
    if abs(dx) >= abs(dy):
        return ("move", "east" if dx > 0 else "west")
    return ("move", "south" if dy > 0 else "north")


def make_bot_config(name: str, emoji: str, alloc: StatAllocation) -> dict[str, Any]:
    """Create a bot config dict for run_match."""
    return {
        "name": name,
        "emoji": emoji,
        "bio": f"{name} archetype",
        "author": "balance_sim",
        "decide_func": _simple_decide,
        "stat_allocation": alloc,
    }


def run_simulation(
    matches_per_combo: int = 20, seed_base: int = 1000,
) -> dict[str, dict[str, Any]]:
    """Run all 4-bot archetype combinations and collect win rates."""
    names = list(ARCHETYPES.keys())
    wins: dict[str, int] = {n: 0 for n in names}
    total_matches: dict[str, int] = {n: 0 for n in names}

    combos = list(itertools.combinations(range(len(names)), 4))

    for combo_idx, combo in enumerate(combos):
        for match_num in range(matches_per_combo):
            seed = seed_base + combo_idx * 1000 + match_num
            configs = [
                make_bot_config(names[i], EMOJIS[i], ARCHETYPES[names[i]])
                for i in combo
            ]
            match_data = run_match(configs, match_id=1, seed=seed)
            winner = match_data.get("winner", match_data.get("winner_emoji", "none"))

            for i in combo:
                total_matches[names[i]] += 1
                if winner == EMOJIS[i]:
                    wins[names[i]] += 1

    results: dict[str, dict[str, Any]] = {}
    for name in names:
        total = total_matches[name]
        w = wins[name]
        rate = (w / total * 100) if total > 0 else 0.0
        results[name] = {"wins": w, "total": total, "win_rate": round(rate, 1)}

    return results


def _print_results(results: dict[str, dict[str, Any]]) -> None:
    """Print formatted results table and balance assessment."""
    print(f"{'Archetype':<15} {'Wins':>6} {'Total':>7} {'Win Rate':>9}")
    print("-" * 40)
    for name, data in sorted(results.items(), key=lambda x: x[1]["win_rate"], reverse=True):
        print(f"{name:<15} {data['wins']:>6} {data['total']:>7} {data['win_rate']:>8.1f}%")

    print()
    max_rate = max(d["win_rate"] for d in results.values())
    balanced_rate = results["Balanced"]["win_rate"]
    print(f"Max win rate: {max_rate}% (target: <55%)")
    print(f"Balanced win rate: {balanced_rate}% (target: 48-52%)")

    if max_rate > 55:
        print("WARNING: IMBALANCED -- An archetype exceeds 55% win rate")
    else:
        print("OK: Balanced -- No archetype exceeds 55%")


def main() -> None:
    """Run the full balance simulation and save results."""
    n_combos = len(list(itertools.combinations(range(7), 4)))
    matches_per = 20
    total = n_combos * matches_per
    print("Running balance simulation...")
    print(f"7 archetypes, C(7,4) = {n_combos} combos x {matches_per} matches = {total} total")
    print()

    results = run_simulation(matches_per_combo=matches_per)
    _print_results(results)

    output_path = Path("tools/balance_results.json")
    output_path.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
