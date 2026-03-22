"""agentgrounds wars watch -- play back a match replay in the terminal."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentgrounds.wars.cli.renderer import TerminalRenderer

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
    p.add_argument(
        "--no-fx", action="store_true",
        help="Disable combat animation sub-frames",
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
    terrain_tiles = match_data.get("terrain_tiles")
    if terrain_tiles is not None:
        renderer.set_terrain(terrain_tiles)

    rounds = match_data.get("rounds", [])
    delay = 1.0 / max(0.01, args.speed)
    action_delay = delay * 0.3
    resolve_delay = delay * 0.7
    clear = not args.no_clear
    no_fx = args.no_fx

    try:
        for round_data in rounds:
            has_combat = (
                not no_fx and TerminalRenderer.has_combat_events(round_data)
            )
            if has_combat:
                action_frame = renderer.render_action_frame(
                    round_data, clear=clear,
                )
                print(action_frame, flush=True)
                time.sleep(action_delay)
            frame = renderer.render_frame(round_data, clear=clear)
            print(frame, flush=True)
            time.sleep(resolve_delay if has_combat else delay)
    except KeyboardInterrupt:
        print(renderer.exit_alt_screen(), end="", flush=True)
        print("\nInterrupted.")
        return

    _show_endgame(renderer, match_data, args.speed)


def _show_endgame(
    renderer: TerminalRenderer, match_data: dict, speed: float,
) -> None:
    """Show final board state then persistent summary in normal scrollback."""
    winner = match_data.get("winner", "?")
    rounds = match_data.get("rounds", [])
    duration = match_data.get("duration_rounds", len(rounds))

    if rounds:
        final_frame = renderer.render_final_frame(rounds[-1], winner)
        print(final_frame, flush=True)
        time.sleep(2.0 / max(0.01, speed))

    print(renderer.exit_alt_screen(), end="", flush=True)
    print(renderer.render_winner(winner, duration))
    print(renderer.render_standings(match_data))


def _load_match(path: Path) -> dict:
    """Load and return match data from a JSON file."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Error reading match file: {exc}", file=sys.stderr)
        sys.exit(1)
