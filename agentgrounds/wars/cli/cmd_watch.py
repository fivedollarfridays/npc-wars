"""agentgrounds wars watch -- play back a match replay in the terminal."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

__all__ = ["register", "run"]


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the watch subcommand."""
    p = subparsers.add_parser("watch", help="Watch a match replay in the terminal")
    p.add_argument("file", help="Path to match JSON file")
    p.add_argument(
        "--speed", type=float, default=1.0,
        help="Playback speed multiplier (default: 1)",
    )
    p.add_argument(
        "--no-clear", action="store_true",
        help="Don't clear screen between frames",
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    """Execute the watch command."""
    path = Path(args.file)
    if not path.is_file():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)

    match_data = _load_match(path)

    from agentgrounds.wars.cli.renderer import TerminalRenderer

    players = match_data.get("players", [])
    grid_size = match_data.get("grid_size", 10)
    renderer = TerminalRenderer(players, grid_size)

    rounds = match_data.get("rounds", [])
    delay = 1.0 / max(0.01, args.speed)
    clear = not args.no_clear

    for round_data in rounds:
        frame = renderer.render_frame(round_data, clear=clear)
        print(frame, flush=True)
        time.sleep(delay)

    winner = match_data.get("winner", "?")
    duration = match_data.get("duration_rounds", len(rounds))
    print(renderer.render_winner(winner, duration))


def _load_match(path: Path) -> dict:
    """Load and return match data from a JSON file."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Error reading match file: {exc}", file=sys.stderr)
        sys.exit(1)
