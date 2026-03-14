#!/usr/bin/env python3
"""Demo: Run an async match with a fake human to see The Cringe in action."""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.loader import load_bots
from engine.game import run_match_async
from engine.watcher import WATCHER_EMOJI, WATCHER_NAME


class FakeHumanAdapter:
    """Pretends to be a human — always attacks north."""

    async def get_action_async(self, state: dict, timeout: float) -> tuple[str, ...]:
        return ("attack", "north")


def _print_spawn_info(match_data: dict) -> None:
    """Print whether The Cringe spawned and when."""
    cringe_spawned = any(
        e.get("type") == "watcher_spawn"
        for r in match_data.get("rounds", [])
        for e in r.get("events", [])
    )
    if cringe_spawned:
        print("🍆 THE CRINGE SPAWNED MID-MATCH!")
        for i, r in enumerate(match_data.get("rounds", []), 1):
            for e in r.get("events", []):
                if e.get("type") == "watcher_spawn":
                    print(f"   Entered at round {i} at position ({e.get('x')}, {e.get('y')})")
    else:
        print("🍆 The Cringe did not spawn (human didn't meet thresholds)")


def _print_kill_feed(match_data: dict, players: dict[str, str]) -> None:
    """Print the kill feed."""
    print("\n💀 Kill Feed:")
    for elim in match_data["eliminations"]:
        killer = elim.get("killed_by", "?")
        victim = elim["emoji"]
        cause = elim["cause"]
        killer_name = players.get(killer, WATCHER_NAME if killer == WATCHER_EMOJI else killer)
        victim_name = players.get(victim, WATCHER_NAME if victim == WATCHER_EMOJI else victim)
        cringe_tag = " 🍆←" if killer == WATCHER_EMOJI else (" →🍆" if victim == WATCHER_EMOJI else "")
        print(f"   R{elim['round']}: {killer} {killer_name} → {victim} {victim_name} ({cause}){cringe_tag}")


def _print_stats(match_data: dict, players: dict[str, str], human_emoji: str) -> None:
    """Print per-bot stats and spectacle events."""
    print("\n📊 Stats:")
    for emoji, stats in match_data["stats"].items():
        name = players.get(emoji, WATCHER_NAME if emoji == WATCHER_EMOJI else "?")
        tag = " [HUMAN]" if emoji == human_emoji else (" [CRINGE]" if emoji == WATCHER_EMOJI else "")
        print(f"   {emoji} {name}{tag} — K:{stats['kills']} DMG:{stats['damage_dealt']} Survived:{stats['rounds_survived']}r")

    cringe_events = []
    for r in match_data.get("rounds", []):
        spec = r.get("spectacle", {})
        for trigger in spec.get("triggers", []):
            if "watcher" in trigger:
                cringe_events.append((r.get("round", "?"), trigger))
    if cringe_events:
        print("\n🎭 Cringe Spectacle Events:")
        for rnd, trigger in cringe_events:
            print(f"   R{rnd}: {trigger}")

    if os.path.exists("data/watcher_memory.json"):
        print("\n💾 Memory saved to data/watcher_memory.json")
    if os.path.exists("data/watcher_stats.json"):
        with open("data/watcher_stats.json") as f:
            ws = json.load(f)
        print(f"💾 Stats: {ws.get('matches', 0)} matches, {ws.get('kills', 0)} kills, {ws.get('deaths', 0)} deaths")


async def main() -> None:
    bots_dir = os.path.join(os.path.dirname(__file__), "bots")

    print("🎮 NPC Wars — The Cringe Demo")
    print("=" * 50)
    bot_configs = load_bots(bots_dir)

    bot_configs[0]["human_adapter"] = FakeHumanAdapter()
    human_name = bot_configs[0]["name"]
    human_emoji = bot_configs[0]["emoji"]
    print(f"   Simulated human: {human_emoji} {human_name}")
    print(f"   Bots: {len(bot_configs) - 1} NPCs")
    print(f"   Boss: {WATCHER_EMOJI} {WATCHER_NAME}\n")

    print("⚔️  MATCH STARTING...\n")
    match_data = await run_match_async(bot_configs, match_id=999, seed=42)

    winner = match_data["winner"]
    duration = match_data["duration_rounds"]
    players = {p["emoji"]: p["name"] for p in match_data["players"]}

    print(f"🏆 WINNER: {winner} {players.get(winner, WATCHER_NAME)}")
    print(f"⏱️  Duration: {duration} rounds\n")

    _print_spawn_info(match_data)
    _print_kill_feed(match_data, players)
    _print_stats(match_data, players, human_emoji)


if __name__ == "__main__":
    asyncio.run(main())
