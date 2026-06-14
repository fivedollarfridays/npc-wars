"""``killswitch doctor <bot.py>`` -- diagnostic report for bot authors.

Runs a target bot against the shipped pool for N seeded matches and reports,
per-run and aggregated: locked/invalid action attempts, plague rounds,
forced-rest (energy-starvation) rounds, storm damage/deaths, and placements.

This is pure wiring over existing engine internals (``run_match``,
``load_bots``) — it adds NO new engine behavior. Exit code is non-zero when
the bot disconnects or attempts any locked action, so CI can fail on it.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from agentgrounds.wars.cli.doctor_report import (
    aggregate_runs,
    analyze_match,
    format_report,
)

__all__ = ["register", "run", "build_diagnostics"]


def _builtin_bots_dir() -> str:
    """Path to the shipped builtin bot pool (the default opponent pool)."""
    return str(Path(__file__).resolve().parent.parent / "builtin_bots")


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the doctor subcommand."""
    p = subparsers.add_parser(
        "doctor",
        help="Diagnose a bot against the shipped pool (locked actions, plague, storm, ...)",
    )
    p.add_argument("bot", type=str, help="Path to the bot .py file to diagnose")
    p.add_argument(
        "--matches", type=int, default=5, help="Number of seeded matches (default: 5)"
    )
    p.add_argument("--seed", type=int, default=1, help="Base seed (default: 1)")
    p.add_argument(
        "--pool-dir", type=str, default=None,
        help="Opponent pool directory (default: shipped builtin pool)",
    )
    p.set_defaults(func=run)


def _read_target_emoji(target_path: str) -> tuple[str, str]:
    """Load the target bot module and return (name, emoji)."""
    from engine.bot_scanner import load_bot_module

    module = load_bot_module(target_path, "doctor_target")
    emoji = getattr(module, "BOT_EMOJI", None)
    name = getattr(module, "BOT_NAME", Path(target_path).stem)
    if not emoji:
        raise ValueError(f"{target_path}: bot is missing BOT_EMOJI")
    return str(name), str(emoji)


def _assemble_pool_dir(target_path: str, pool_dir: str, emoji: str, workdir: str) -> str:
    """Build a temp dir = pool bots (minus any emoji clash) + the target bot.

    The target is copied LAST under a name that loads first, and any pool file
    declaring the same emoji is dropped, so the loader keeps the target's bot.
    """
    dest = Path(workdir)
    # Copy pool bots that do not collide with the target emoji.
    for f in sorted(Path(pool_dir).glob("*.py")):
        if f.name.startswith("_") or f.name == "template.py":
            continue
        if _file_emoji(str(f)) == emoji:
            continue
        shutil.copy(str(f), dest / f.name)
    # Copy the target with a name that sorts first (loader keeps first-seen).
    shutil.copy(target_path, dest / f"00_target_{Path(target_path).name}")
    return str(dest)


def _file_emoji(path: str) -> str | None:
    """Best-effort read of a bot file's BOT_EMOJI (None if unreadable)."""
    from engine.bot_scanner import load_bot_module

    try:
        module = load_bot_module(path, f"probe_{Path(path).stem}")
    except Exception:
        return None
    return getattr(module, "BOT_EMOJI", None)


def _run_pool_matches(
    bots_dir: str, matches: int, seed: int
) -> list[dict[str, Any]]:
    """Run N seeded matches over the assembled pool; return raw match_data list."""
    from engine.game import run_match
    from engine.loader import load_bots

    bot_configs = load_bots(bots_dir)
    if len(bot_configs) < 2:
        raise ValueError("need at least 2 valid bots in the pool")
    results: list[dict[str, Any]] = []
    for i in range(1, matches + 1):
        results.append(run_match(bot_configs, match_id=i, seed=seed + i))
    return results


def build_diagnostics(
    target_path: str, pool_dir: str, matches: int, seed: int
) -> dict[str, Any]:
    """Run the target bot against the pool and build the diagnostic report dict."""
    name, emoji = _read_target_emoji(target_path)
    with tempfile.TemporaryDirectory(prefix="doctor_pool_") as workdir:
        bots_dir = _assemble_pool_dir(target_path, pool_dir, emoji, workdir)
        match_results = _run_pool_matches(bots_dir, matches, seed)

    runs = [analyze_match(md, emoji) for md in match_results]
    agg = aggregate_runs(runs)
    healthy = agg["locked_action_attempts"] == 0 and agg["disconnects"] == 0
    return {
        "name": name,
        "emoji": emoji,
        "pool_dir": pool_dir,
        "matches": matches,
        "seed": seed,
        "runs": runs,
        "aggregate": agg,
        "healthy": healthy,
    }


def run(args: argparse.Namespace) -> None:
    """CLI entry point for ``killswitch doctor``."""
    target = args.bot
    if not Path(target).is_file():
        print(f"Error: bot file '{target}' not found", file=sys.stderr)
        sys.exit(2)

    pool_dir = args.pool_dir or _builtin_bots_dir()
    if not Path(pool_dir).is_dir():
        print(f"Error: pool directory '{pool_dir}' not found", file=sys.stderr)
        sys.exit(2)

    try:
        report = build_diagnostics(target, pool_dir, args.matches, args.seed)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    print(format_report(report))
    sys.exit(0 if report["healthy"] else 1)
