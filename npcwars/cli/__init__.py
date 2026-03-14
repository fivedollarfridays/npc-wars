"""NPC Wars CLI — unified command-line interface."""
from __future__ import annotations

import argparse
import sys

__all__ = ["main"]


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="npcwars",
        description="NPC Wars — autonomous bot battle royale",
    )
    try:
        from importlib.metadata import PackageNotFoundError, version

        ver = version("npc-wars")
    except PackageNotFoundError:
        ver = "dev"
    parser.add_argument("--version", action="version", version=f"npcwars {ver}")

    subs = parser.add_subparsers(dest="subcommand")

    from npcwars.cli import cmd_init

    cmd_init.register(subs)

    from npcwars.cli import cmd_wizard

    cmd_wizard.register(subs)

    from npcwars.cli import cmd_validate

    cmd_validate.register(subs)

    from npcwars.cli import cmd_battle

    cmd_battle.register(subs)

    return parser


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.subcommand is None:
        parser.print_help()
        sys.exit(2)
    args.func(args)


if __name__ == "__main__":
    main()
