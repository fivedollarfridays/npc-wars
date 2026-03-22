"""Ability balance simulation -- run bots including ability-using mage."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.game import run_match  # noqa: E402
from engine.loader import load_bots  # noqa: E402


def build_mage_config() -> dict[str, Any]:
    """Build a mage bot config with callback references for ability wiring."""
    from bots.example_mage import (
        BOT_AUTHOR, BOT_BIO, BOT_EMOJI, BOT_EQUIPMENT, BOT_NAME,
        decide, evolve, power_up,
    )
    from engine.stats import validate_allocation

    return {
        "name": BOT_NAME,
        "emoji": BOT_EMOJI,
        "bio": BOT_BIO,
        "author": BOT_AUTHOR,
        "decide_func": decide,
        "stat_allocation": validate_allocation(15, 20, 20, 45),
        "equipment": dict(BOT_EQUIPMENT),
        "callbacks": {"power_up": power_up, "evolve": evolve},
        "unlocked_actions": sorted({"move", "attack", "rest", "defend",
                                     "use_ability"}),
    }


def run_simulation(
    n_matches: int = 200, seed_base: int = 8000,
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

    # Wire mage callbacks and unlock use_ability for all bots
    _ABILITY_ACTIONS = sorted({"move", "attack", "rest", "defend",
                                "ranged_attack", "dash", "taunt",
                                "trap", "use_ability", "use_tactical"})
    for b in all_bots:
        b["unlocked_actions"] = list(_ABILITY_ACTIONS)
        if b["name"] == "Mage":
            from bots.example_mage import evolve, power_up
            b["callbacks"] = {"power_up": power_up, "evolve": evolve}

    for match_num in range(n_matches):
        k = rng.randint(4, min(6, len(all_bots)))
        chosen_indices = rng.sample(range(len(all_bots)), k)
        seed = seed_base + match_num
        configs = [all_bots[i] for i in chosen_indices]

        result = _run_match_with_callbacks(configs, match_num, seed)
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


def _run_match_with_callbacks(
    configs: list[dict[str, Any]], match_num: int, seed: int,
) -> dict[str, Any]:
    """Run a match, wiring callbacks onto Bot objects post-creation.

    The standard run_match doesn't wire bot callbacks from configs,
    so we monkey-patch the game's _create_bots to set them after creation.
    """
    import engine.game as game_mod
    original_create = game_mod._create_bots

    # Map of emoji -> callbacks dict
    callback_map = {
        c["emoji"]: c["callbacks"]
        for c in configs if "callbacks" in c
    }

    def _patched_create(bot_configs, positions):
        bots = original_create(bot_configs, positions)
        if callback_map:
            from engine.callbacks import CallbackSet
            for bot in bots:
                cbs = callback_map.get(bot.emoji)
                if cbs:
                    bot.callbacks = CallbackSet(**cbs)
        return bots

    game_mod._create_bots = _patched_create  # type: ignore[assignment]
    try:
        return run_match(configs, match_id=match_num, seed=seed)
    finally:
        game_mod._create_bots = original_create  # type: ignore[assignment]


def main() -> None:
    n = 200
    print(f"Running ability balance simulation ({n} matches)...")
    results = run_simulation(n_matches=n)

    print(f"\n{'Bot':<15} {'Wins':>6} {'Total':>7} {'Win Rate':>9}")
    print("-" * 40)
    for name, data in sorted(
        results.items(), key=lambda x: x[1]["win_rate"], reverse=True,
    ):
        print(f"{name:<15} {data['wins']:>6} {data['total']:>7} "
              f"{data['win_rate']:>8.1f}%")

    output = Path("tools/ability_balance_results.json")
    output.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {output}")


if __name__ == "__main__":
    main()
