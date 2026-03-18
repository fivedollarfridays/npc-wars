"""agentgrounds wars play -- validate, battle, and watch in one command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

__all__ = ["register", "run"]


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the play subcommand."""
    p = subparsers.add_parser(
        "play", help="Run a match and watch it in the terminal",
    )
    p.add_argument(
        "--bots-dir", type=str, default="bots",
        help="Bots directory (default: bots)",
    )
    p.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for deterministic matches",
    )
    p.add_argument(
        "--speed", type=float, default=1.0,
        help="Playback speed multiplier (default: 1)",
    )
    p.add_argument(
        "--no-watch", action="store_true",
        help="Skip terminal playback, just print summary",
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    """Execute the play command."""
    bots_dir = Path(args.bots_dir)
    if not bots_dir.is_dir():
        print(f"Error: bots directory '{bots_dir}' not found", file=sys.stderr)
        sys.exit(1)

    # 1. Validate all bots
    if not _validate_bots(bots_dir):
        sys.exit(1)

    # 2. Load and run match
    match_data, filepath = _run_match(bots_dir, args.seed)

    # 3. Display results
    if args.no_watch:
        _print_summary(match_data, filepath)
        return

    _play_back(match_data, args.speed, filepath)


def _validate_bots(bots_dir: Path) -> bool:
    """Validate all bot files in the directory. Returns True if all pass."""
    from scripts.validate_bot import validate_bot

    bot_files = sorted(bots_dir.glob("*.py"))
    bot_files = [f for f in bot_files if f.name not in ("template.py", "__init__.py")]

    errors_found = False
    for bf in bot_files:
        ok, errs = validate_bot(str(bf))
        if not ok:
            print(f"  FAIL  {bf.name}: {errs[0]}")
            errors_found = True

    if errors_found:
        print("\nFix validation errors before playing.", file=sys.stderr)
        return False
    return True


def _run_match(bots_dir: Path, seed: int | None) -> tuple[dict, str]:
    """Load bots, run a match, write replay. Returns (match_data, filepath)."""
    from data.match_history import next_match_id
    from data.stat_diff import inject_diff_data
    from engine.game import run_match
    from engine.loader import load_bots
    from engine.match_writer import write_match

    bot_configs = load_bots(str(bots_dir))
    if len(bot_configs) < 2:
        print("Error: need at least 2 valid bots", file=sys.stderr)
        sys.exit(1)

    results_dir = "results"
    match_id = next_match_id(results_dir)
    match_data = run_match(bot_configs, match_id=match_id, seed=seed)
    inject_diff_data(match_data, results_dir)
    filepath = write_match(match_data, results_dir)
    return match_data, filepath


def _print_summary(match_data: dict, filepath: str) -> None:
    """Print a one-line match summary."""
    winner = match_data.get("winner", "?")
    duration = match_data.get("duration_rounds", 0)
    print(f"Winner: {winner} | Rounds: {duration} | Saved: {filepath}")


def _play_back(match_data: dict, speed: float, filepath: str) -> None:
    """Play back the match in the terminal with ANSI renderer."""
    import time

    from agentgrounds.wars.cli.renderer import TerminalRenderer

    players = match_data.get("players", [])
    grid_size = match_data.get("grid_size", 10)
    renderer = TerminalRenderer(players, grid_size)

    delay = 1.0 / max(0.01, speed)
    for round_data in match_data.get("rounds", []):
        frame = renderer.render_frame(round_data, clear=True)
        print(frame, flush=True)
        time.sleep(delay)

    winner = match_data.get("winner", "?")
    duration = match_data.get("duration_rounds", 0)
    print(renderer.render_winner(winner, duration))
    print(f"  Replay saved: {filepath}")
    print(f"  Re-watch: agentgrounds wars watch {filepath} --speed 4")
