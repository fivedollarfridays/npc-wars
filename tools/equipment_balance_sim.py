"""Equipment balance simulation -- run bots with equipment loadouts."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.game import run_match  # noqa: E402
from engine.loader import load_bots  # noqa: E402


def run_simulation(
    n_matches: int = 200, seed_base: int = 7000,
) -> dict[str, dict[str, Any]]:
    """Run random-subset matches and collect per-bot stats."""
    bots_dir = str(Path(__file__).resolve().parent.parent / "bots")
    all_bots = load_bots(bots_dir)
    if len(all_bots) < 4:
        print(f"Need at least 4 bots, found {len(all_bots)}")
        sys.exit(1)

    names = [b["name"] for b in all_bots]
    wins: dict[str, int] = {n: 0 for n in names}
    total: dict[str, int] = {n: 0 for n in names}
    rng = random.Random(seed_base)

    for match_num in range(n_matches):
        # Random 4-6 bot subset
        k = rng.randint(4, min(6, len(all_bots)))
        chosen_indices = rng.sample(range(len(all_bots)), k)
        seed = seed_base + match_num
        configs = [all_bots[i] for i in chosen_indices]

        result = run_match(configs, match_id=match_num, seed=seed)
        winner_emoji = result.get("winner", "none")

        for i in chosen_indices:
            total[names[i]] += 1
            if winner_emoji == all_bots[i]["emoji"]:
                wins[names[i]] += 1

    results: dict[str, dict[str, Any]] = {}
    for name in names:
        t = total[name]
        w = wins[name]
        rate = (w / t * 100) if t > 0 else 0.0
        results[name] = {"wins": w, "total": t, "win_rate": round(rate, 1)}
    return results


def main() -> None:
    n = 200
    print(f"Running equipment balance simulation ({n} matches)...")
    results = run_simulation(n_matches=n)

    print(f"\n{'Bot':<15} {'Wins':>6} {'Total':>7} {'Win Rate':>9}")
    print("-" * 40)
    for name, data in sorted(
        results.items(), key=lambda x: x[1]["win_rate"], reverse=True,
    ):
        print(f"{name:<15} {data['wins']:>6} {data['total']:>7} {data['win_rate']:>8.1f}%")

    output = Path("tools/equipment_balance_results.json")
    output.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {output}")


if __name__ == "__main__":
    main()
