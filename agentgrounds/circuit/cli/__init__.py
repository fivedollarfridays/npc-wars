"""Agent Grounds Circuit CLI — unified command-line interface."""

from __future__ import annotations

import argparse
import sys

__all__ = ["main"]


def _register_subcommands(subs: argparse._SubParsersAction) -> None:
    """Register all Circuit CLI subcommands."""
    from agentgrounds.circuit.cli import cmd_race

    cmd_race.register(subs)


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="agentgrounds circuit",
        description="Agent Grounds Circuit — autonomous bot racing",
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
