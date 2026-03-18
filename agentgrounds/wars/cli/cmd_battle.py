"""agentgrounds wars battle -- run a bot battle."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

__all__ = ["register", "run"]


def register(subparser: argparse._SubParsersAction) -> None:
    """Register the battle subcommand."""
    p = subparser.add_parser("battle", help="Run a bot battle")
    p.add_argument(
        "--bots-dir", type=str, default=None,
        help="Directory containing bots (default: from config)",
    )
    p.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for deterministic matches",
    )
    p.add_argument(
        "--replay", type=str, default=None,
        help="Directory to save match replay JSON",
    )
    p.set_defaults(func=run)


def _resolve_config(args: argparse.Namespace) -> tuple[str, int | None, str | None]:
    """Resolve bots_dir, seed, replay_dir from args and config file."""
    from agentgrounds.wars.config import CONFIG_FILENAME, load_config

    config = load_config(Path(CONFIG_FILENAME))
    bots_dir = args.bots_dir or config["bots_dir"]
    seed = args.seed if args.seed is not None else config.get("seed")
    replay_dir = args.replay
    return bots_dir, seed, replay_dir


def _print_summary(match_data: dict) -> None:
    """Print match results to stdout."""
    winner = match_data["winner"]
    duration = match_data["duration_rounds"]
    player = next((p for p in match_data["players"] if p["emoji"] == winner), None)
    name = player["name"] if player else "?"
    print(f"\nWinner: {winner} {name}")
    print(f"Rounds: {duration}")
    print("\nKill Feed:")
    for elim in match_data.get("eliminations", []):
        killed_by = elim.get("killed_by", "?")
        print(f"  R{elim['round']}: {killed_by} eliminated {elim['emoji']} ({elim['cause']})")


def run(args: argparse.Namespace) -> None:
    """Execute the battle command."""
    bots_dir, seed, replay_dir = _resolve_config(args)

    bots_path = Path(bots_dir)
    if not bots_path.is_dir():
        print(f"Error: bots directory not found: {bots_dir}", file=sys.stderr)
        sys.exit(1)

    from engine.loader import load_bots

    bot_configs = load_bots(str(bots_path))

    if len(bot_configs) < 2:
        print(
            f"Error: need at least 2 bots, found {len(bot_configs)}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Agent Grounds Wars -- {len(bot_configs)} bots loaded")
    for b in bot_configs:
        print(f"  {b['emoji']} {b['name']}")

    from engine.game import run_match

    match_data = run_match(bot_configs, match_id=1, seed=seed)

    _print_summary(match_data)

    if replay_dir:
        replay_path = Path(replay_dir)
        replay_path.mkdir(parents=True, exist_ok=True)
        from data.stat_diff import inject_diff_data
        from engine.match_writer import write_match

        inject_diff_data(match_data, str(replay_path))  # diff only for replay files
        filepath = write_match(match_data, str(replay_path))
        print(f"\nReplay saved: {filepath}")
