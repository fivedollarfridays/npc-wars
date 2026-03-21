"""Trap balance simulation — compare trapper bot vs standard archetypes."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.game import run_match  # noqa: E402
from engine.stats import StatAllocation  # noqa: E402


def _simple_decide(state: dict[str, Any]) -> tuple[str, ...]:
    """Simple bot AI for balance testing."""
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


def _trap_decide(state: dict[str, Any]) -> tuple[str, ...]:
    """Trap-using bot AI for balance testing."""
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

    # Place trap toward nearest enemy if cooldown ready
    if me.get("trap_cooldown", 0) == 0 and me["energy"] >= 15 and dist <= 4:
        if abs(dx) > abs(dy):
            return ("trap", "east" if dx > 0 else "west")
        return ("trap", "south" if dy > 0 else "north")

    if dist == 1:
        if abs(dx) > abs(dy):
            direction = "east" if dx > 0 else "west"
        else:
            direction = "south" if dy > 0 else "north"
        return ("attack", direction)
    if abs(dx) >= abs(dy):
        return ("move", "east" if dx > 0 else "west")
    return ("move", "south" if dy > 0 else "north")


BOTS: dict[str, dict[str, Any]] = {
    "Balanced": {"alloc": StatAllocation(25, 25, 25, 25), "decide": _simple_decide,
                 "actions": sorted(["move", "attack", "rest", "defend"])},
    "Bruiser": {"alloc": StatAllocation(35, 15, 35, 15), "decide": _simple_decide,
                "actions": sorted(["move", "attack", "rest", "defend"])},
    "Assassin": {"alloc": StatAllocation(20, 50, 15, 15), "decide": _simple_decide,
                 "actions": sorted(["move", "attack", "rest", "defend"])},
    "Tank": {"alloc": StatAllocation(15, 15, 50, 20), "decide": _simple_decide,
             "actions": sorted(["move", "attack", "rest", "defend"])},
    "Trapper": {"alloc": StatAllocation(35, 20, 25, 20), "decide": _trap_decide,
                "actions": sorted(["move", "attack", "rest", "defend", "trap"])},
}

EMOJIS = ["🔴", "🔵", "🟢", "🟡", "🟣"]


def run_simulation(n_matches: int = 200, seed_base: int = 5000) -> dict[str, dict[str, Any]]:
    """Run random-subset matches and collect stats."""
    names = list(BOTS.keys())
    wins: dict[str, int] = {n: 0 for n in names}
    total: dict[str, int] = {n: 0 for n in names}
    trap_events: dict[str, int] = {"placed": 0, "triggered": 0, "kills": 0}
    rng = random.Random(seed_base)

    for match_num in range(n_matches):
        # Random 4-bot subset
        chosen = rng.sample(range(len(names)), min(4, len(names)))
        seed = seed_base + match_num
        configs = []
        for i in chosen:
            configs.append({
                "name": names[i], "emoji": EMOJIS[i],
                "bio": f"{names[i]} archetype", "author": "trap_sim",
                "decide_func": BOTS[names[i]]["decide"],
                "stat_allocation": BOTS[names[i]]["alloc"],
                "unlocked_actions": BOTS[names[i]]["actions"],
            })

        result = run_match(configs, match_id=match_num, seed=seed)
        winner = result.get("winner", "none")

        for i in chosen:
            total[names[i]] += 1
            if winner == EMOJIS[i]:
                wins[names[i]] += 1

        # Count trap events
        for rnd in result.get("rounds", []):
            for evt in rnd.get("events", []):
                if evt.get("type") == "trap_placed":
                    trap_events["placed"] += 1
                elif evt.get("type") == "trap_trigger":
                    trap_events["triggered"] += 1
                elif evt.get("type") == "kill" and evt.get("killed_by_trap"):
                    trap_events["kills"] += 1

    results: dict[str, dict[str, Any]] = {}
    for name in names:
        t = total[name]
        w = wins[name]
        rate = (w / t * 100) if t > 0 else 0.0
        results[name] = {"wins": w, "total": t, "win_rate": round(rate, 1)}
    results["_trap_events"] = trap_events  # type: ignore[assignment]
    return results


def main() -> None:
    n = 200
    print(f"Running trap balance simulation ({n} matches)...")
    results = run_simulation(n_matches=n)

    print(f"\n{'Bot':<15} {'Wins':>6} {'Total':>7} {'Win Rate':>9}")
    print("-" * 40)
    for name, data in sorted(
        ((k, v) for k, v in results.items() if k != "_trap_events"),
        key=lambda x: x[1]["win_rate"], reverse=True,
    ):
        print(f"{name:<15} {data['wins']:>6} {data['total']:>7} {data['win_rate']:>8.1f}%")

    trap_data = results.get("_trap_events", {})
    print(f"\nTrap events: {trap_data.get('placed', 0)} placed, "
          f"{trap_data.get('triggered', 0)} triggered")

    output = Path("tools/trap_balance_results.json")
    output.write_text(json.dumps(results, indent=2))
    print(f"Results saved to {output}")


if __name__ == "__main__":
    main()
