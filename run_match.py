#!/usr/bin/env python3
"""Run an NPC Wars match."""

import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.loader import load_bots
from engine.game import run_match
from engine.match_writer import write_match
from engine.xp_runner import inject_xp_into_match


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run an NPC Wars match")
    parser.add_argument("--no-xp", action="store_true", help="Skip XP tracking")
    parser.add_argument("--db-path", type=str, default=None, help="Profile DB path (default: data/profiles.db)")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    bots_dir = os.path.join(os.path.dirname(__file__), "bots")
    results_dir = os.path.join(os.path.dirname(__file__), "results")

    print("NPC Wars -- Loading bots...")
    bot_configs = load_bots(bots_dir)
    print(f"   Loaded {len(bot_configs)} bots:")
    for b in bot_configs:
        print(f"   {b['emoji']} {b['name']} -- {b['bio']}")

    if len(bot_configs) < 2:
        print("Error: Need at least 2 bots to fight!")
        return

    print(f"\n  MATCH #1 STARTING -- {len(bot_configs)} bots locked in\n")

    match_data = run_match(bot_configs, match_id=1)

    # XP integration: calculate, persist, inject into match result
    inject_xp_into_match(match_data, db_path=args.db_path, no_xp=args.no_xp)

    filepath = write_match(match_data, results_dir)
    print(f"\nMatch data written to: {filepath}")

    # Print results
    winner = match_data["winner"]
    duration = match_data["duration_rounds"]
    print(f"\nWINNER: {winner}")
    print(f"Duration: {duration} rounds\n")

    print("Kill Feed:")
    for elim in match_data["eliminations"]:
        print(f"   R{elim['round']}: {elim.get('killed_by', '?')} -> {elim['emoji']} ({elim['cause']})")

    print("\nStats:")
    for emoji, stats in match_data["stats"].items():
        print(f"   {emoji} -- K:{stats['kills']} DMG:{stats['damage_dealt']} Survived:{stats['rounds_survived']}r")

    _print_xp_summary(match_data)


def _print_xp_summary(match_data: dict) -> None:
    """Print XP summary if xp_awards present."""
    xp_awards = match_data.get("xp_awards")
    if not xp_awards:
        return
    print("\nXP Awards:")
    for emoji, award in xp_awards.items():
        level_tag = f" -> Level {award['new_level']}!" if award["leveled_up"] else ""
        print(f"   {emoji} +{award['total']} XP (L{award['new_level']}){level_tag}")


if __name__ == "__main__":
    main()
