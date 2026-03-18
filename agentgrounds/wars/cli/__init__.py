"""Agent Grounds Wars CLI — unified command-line interface."""
from __future__ import annotations

import argparse
import sys

__all__ = ["main"]


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="agentgrounds wars",
        description="Agent Grounds Wars — autonomous bot battle royale",
    )
    try:
        from importlib.metadata import PackageNotFoundError, version

        ver = version("agent-grounds")
    except PackageNotFoundError:
        ver = "dev"
    parser.add_argument("--version", action="version", version=f"agentgrounds {ver}")

    subs = parser.add_subparsers(dest="subcommand")

    from agentgrounds.wars.cli import cmd_init

    cmd_init.register(subs)

    from agentgrounds.wars.cli import cmd_wizard

    cmd_wizard.register(subs)

    from agentgrounds.wars.cli import cmd_validate

    cmd_validate.register(subs)

    from agentgrounds.wars.cli import cmd_battle

    cmd_battle.register(subs)

    from agentgrounds.wars.cli import cmd_watch

    cmd_watch.register(subs)

    from agentgrounds.wars.cli import cmd_generate

    cmd_generate.register(subs)

    from agentgrounds.wars.cli import cmd_play

    cmd_play.register(subs)

    from agentgrounds.wars.cli import cmd_sim

    cmd_sim.register(subs)

    from agentgrounds.wars.cli import cmd_analyze

    cmd_analyze.register(subs)

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
