#!/usr/bin/env python3
"""Run an NPC Wars match."""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.loader import load_bots
from engine.game import run_match
from engine.match_writer import write_match


def main():
    bots_dir = os.path.join(os.path.dirname(__file__), "bots")
    results_dir = os.path.join(os.path.dirname(__file__), "results")

    print("🎮 NPC Wars — Loading bots...")
    bot_configs = load_bots(bots_dir)
    print(f"   Loaded {len(bot_configs)} bots:")
    for b in bot_configs:
        print(f"   {b['emoji']} {b['name']} — {b['bio']}")

    if len(bot_configs) < 2:
        print("❌ Need at least 2 bots to fight!")
        return

    print(f"\n⚔️  MATCH #1 STARTING — {len(bot_configs)} bots locked in\n")

    match_data = run_match(bot_configs, match_id=1)

    filepath = write_match(match_data, results_dir)
    print(f"\n📁 Match data written to: {filepath}")

    # Print results
    winner = match_data["winner"]
    duration = match_data["duration_rounds"]
    print(f"\n🏆 WINNER: {winner}")
    print(f"⏱️  Duration: {duration} rounds\n")

    print("💀 Kill Feed:")
    for elim in match_data["eliminations"]:
        print(f"   R{elim['round']}: {elim.get('killed_by', '?')} → {elim['emoji']} ({elim['cause']})")

    print("\n📊 Stats:")
    for emoji, stats in match_data["stats"].items():
        print(f"   {emoji} — K:{stats['kills']} DMG:{stats['damage_dealt']} Survived:{stats['rounds_survived']}r")


if __name__ == "__main__":
    main()
