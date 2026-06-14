"""Agent Grounds Wars CLI — unified command-line interface."""
from __future__ import annotations

import argparse
import sys

__all__ = ["main"]


def _register_subcommands(subs: argparse._SubParsersAction) -> None:
    """Register all CLI subcommands."""
    from agentgrounds.wars.cli import (
        cmd_analyze,
        cmd_battle,
        cmd_doctor,
        cmd_generate,
        cmd_init,
        cmd_leaderboard,
        cmd_play,
        cmd_profile,
        cmd_sim,
        cmd_upload,
        cmd_validate,
        cmd_watch,
        cmd_watch_web,
        cmd_wizard,
    )

    for cmd in (
        cmd_init, cmd_wizard, cmd_validate, cmd_battle, cmd_watch, cmd_watch_web,
        cmd_generate, cmd_play, cmd_sim, cmd_analyze, cmd_profile,
        cmd_upload, cmd_leaderboard, cmd_doctor,
    ):
        cmd.register(subs)


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
    _register_subcommands(subs)
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
