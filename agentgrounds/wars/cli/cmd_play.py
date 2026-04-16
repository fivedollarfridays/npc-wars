"""agentgrounds killswitch play -- validate, battle, and watch in one command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentgrounds.wars.cli.renderer import TerminalRenderer

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
    p.add_argument(
        "--no-fx", action="store_true",
        help="Disable combat animation sub-frames",
    )
    p.add_argument(
        "--no-tv", action="store_true",
        help="Skip TV generation (commentary, highlights, profiles, rivalries)",
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
    match_data, filepath = _run_match(bots_dir, args.seed, no_tv=args.no_tv)

    # 3. Display results
    if args.no_watch:
        _print_summary(match_data, filepath)
        return

    _play_back(match_data, args.speed, filepath, no_fx=args.no_fx)


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


def _run_match(
    bots_dir: Path, seed: int | None, *, no_tv: bool = False,
) -> tuple[dict, str]:
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

    if not no_tv:
        from engine.tv_pipeline import enrich_tv

        enrich_tv(match_data, results_dir=results_dir)

    filepath = write_match(match_data, results_dir)
    return match_data, filepath


def _print_summary(match_data: dict, filepath: str) -> None:
    """Print rich match summary with kill feed, stats, and diff."""
    winner = match_data.get("winner", "?")
    duration = match_data.get("duration_rounds", 0)
    stats = match_data.get("stats", {})
    elims = match_data.get("eliminations", [])

    # Find winner name
    players = match_data.get("players", [])
    winner_name = next((p["name"] for p in players if p["emoji"] == winner), winner)

    print(f"\n  WINNER: {winner} {winner_name}")
    print(f"  Duration: {duration} rounds\n")

    # Kill feed (last 8)
    if elims:
        print("  Kill Feed:")
        for e in elims[-8:]:
            print(f"    R{e.get('round', '?')}: {e.get('killed_by', '?')} → {e.get('emoji', '?')} ({e.get('cause', '?')})")
        print()

    # Top stats
    if stats:
        print("  Stats:")
        for emoji, s in sorted(stats.items(), key=lambda x: x[1].get("kills", 0), reverse=True)[:5]:
            print(f"    {emoji}  K:{s.get('kills',0)}  DMG:{s.get('damage_dealt',0)}  Survived:{s.get('rounds_survived',0)}r")
        print()

    # Diff summary for winner
    diff = match_data.get("diff", {})
    if diff and winner in diff:
        wd = diff[winner]
        if wd.get("first_match"):
            print("  First match! Play again to see your improvement.\n")
        else:
            print("  Stats vs Lifetime Average:")
            for key in ("win_rate", "avg_kills", "avg_rounds_survived", "avg_damage_dealt"):
                if key in wd:
                    d = wd[key]
                    cls = d.get("classification", "")
                    arrow = "▲" if cls == "improved" else "▼" if cls == "regressed" else "─"
                    print(f"    {key}: {arrow} {d.get('current', '?')}")
            print()

    print(f"  Saved: {filepath}")
    print(f"  Watch: agentgrounds killswitch watch {filepath}")
    print("\n  Edit your bot and play again! →  agentgrounds killswitch play\n")


def _play_back(
    match_data: dict,
    speed: float,
    filepath: str,
    *,
    no_fx: bool = False,
) -> None:
    """Play back the match in the terminal with ANSI renderer."""
    import time

    from agentgrounds.wars.cli.renderer import TerminalRenderer

    players = match_data.get("players", [])
    grid_size = match_data.get("grid_size", 10)
    renderer = TerminalRenderer(players, grid_size)
    terrain_tiles = match_data.get("terrain_tiles")
    if terrain_tiles is not None:
        renderer.set_terrain(terrain_tiles)

    delay = 1.0 / max(0.01, speed)
    action_delay = delay * 0.3
    resolve_delay = delay * 0.7

    try:
        for round_data in match_data.get("rounds", []):
            has_combat = (
                not no_fx and TerminalRenderer.has_combat_events(round_data)
            )
            if has_combat:
                action_frame = renderer.render_action_frame(
                    round_data, clear=True,
                )
                print(action_frame, flush=True)
                time.sleep(action_delay)
            frame = renderer.render_frame(round_data, clear=True)
            print(frame, flush=True)
            time.sleep(resolve_delay if has_combat else delay)
    except KeyboardInterrupt:
        print(renderer.exit_alt_screen(), end="", flush=True)
        print("\nInterrupted.")
        return

    _show_endgame(renderer, match_data, speed, filepath)


def _show_endgame(
    renderer: TerminalRenderer, match_data: dict, speed: float, filepath: str,
) -> None:
    """Show final board state then persistent summary in normal scrollback."""
    import time

    winner = match_data.get("winner", "?")
    duration = match_data.get("duration_rounds", 0)
    rounds = match_data.get("rounds", [])

    # Show final board state in alt screen with winner highlighted
    if rounds:
        final_frame = renderer.render_final_frame(rounds[-1], winner)
        print(final_frame, flush=True)
        time.sleep(2.0 / max(0.01, speed))

    # Exit alt screen, print persistent summary to normal scrollback
    print(renderer.exit_alt_screen(), end="", flush=True)
    print(renderer.render_winner(winner, duration))
    print(renderer.render_standings(match_data))
    print(f"  Replay saved: {filepath}")
    print(f"  Re-watch: agentgrounds killswitch watch {filepath} --speed 4")
