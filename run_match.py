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
    _print_diff_summary(match_data, results_dir)


def _print_diff_summary(match_data: dict, results_dir: str) -> None:
    """Print post-match diff for each bot."""
    from agentgrounds.wars.cli.diff_display import format_match_summary
    from data.lifetime_stats import get_all_lifetime_stats
    from data.stat_diff import compute_diff

    lifetime = get_all_lifetime_stats(results_dir)
    xp_awards = match_data.get("xp_awards", {})
    stats = match_data.get("stats", {})
    players = match_data.get("players", [])
    winner = match_data.get("winner", "none")

    # Show diff for winner only (keep output clean)
    if winner == "none":
        return
    player = next((p for p in players if p["emoji"] == winner), None)
    if not player:
        return

    emoji = winner
    bot_stats = stats.get(emoji, {})
    current = {
        "win_rate": 100.0,
        "avg_kills": float(bot_stats.get("kills", 0)),
        "avg_rounds_survived": float(bot_stats.get("rounds_survived", 0)),
        "avg_damage_dealt": float(bot_stats.get("damage_dealt", 0)),
    }
    diff_data = compute_diff(lifetime.get(emoji), current)
    xp = xp_awards.get(emoji)
    old_level = (xp.get("new_level", 1) - (1 if xp.get("leveled_up") else 0)) if xp else 1
    new_level = xp.get("new_level", 1) if xp else 1

    print(format_match_summary(
        bot_name=player.get("name", emoji), bot_glyph=player.get("glyph", emoji),
        placement=1, kills=bot_stats.get("kills", 0),
        rounds_survived=bot_stats.get("rounds_survived", 0),
        score=int(bot_stats.get("score", 0)),
        momentum_name=bot_stats.get("momentum_name", ""),
        diff_data=diff_data, xp_data=xp,
        old_level=old_level, new_level=new_level,
    ))


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
