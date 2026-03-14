"""npcwars init — scaffold a new NPC Wars arena."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

__all__ = ["register", "run"]


def register(subparser: argparse._SubParsersAction) -> None:
    """Register the init subcommand."""
    p = subparser.add_parser("init", help="Initialize a new NPC Wars arena")
    p.add_argument(
        "--dir", type=str, default=".", help="Target directory (default: current)"
    )
    p.add_argument(
        "--force", action="store_true", help="Overwrite existing files"
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    """Execute the init command."""
    from npcwars.builtin_bots import get_bot_source, list_builtin_bots
    from npcwars.config import CONFIG_FILENAME, write_default_config

    target = Path(args.dir).resolve()
    bots_dir = target / "bots"
    replays_dir = target / "replays"
    config_path = target / CONFIG_FILENAME

    if bots_dir.exists() and not args.force:
        print(f"Arena already initialized at {target} (use --force to overwrite)")
        sys.exit(0)

    # Create directories
    bots_dir.mkdir(parents=True, exist_ok=True)
    replays_dir.mkdir(parents=True, exist_ok=True)

    # Copy built-in bots
    bot_names = list_builtin_bots()
    for name in bot_names:
        bot_path = bots_dir / f"{name}.py"
        if bot_path.exists() and not args.force:
            continue
        bot_path.write_text(get_bot_source(name), encoding="utf-8")

    # Write default config
    if not config_path.exists() or args.force:
        write_default_config(config_path)

    print(f"Initialized NPC Wars arena at {target}")
    print(f"  bots/        — {len(bot_names)} starter bots")
    print("  replays/     — match recordings")
    print("  npcwars.toml — configuration")
    print("\nNext: npcwars wizard   (create your own bot)")
    print("      npcwars battle   (run a match)")
