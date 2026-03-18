"""agentgrounds wars wizard -- interactive bot builder."""
from __future__ import annotations

import argparse

__all__ = ["register", "run"]


def register(subparser: argparse._SubParsersAction) -> None:
    """Register the wizard subcommand."""
    p = subparser.add_parser("wizard", help="Interactive bot builder")
    p.add_argument("--non-interactive", action="store_true")
    p.add_argument("--name", type=str, default="")
    p.add_argument("--emoji", type=str, default="")
    p.add_argument("--style", type=str, default="")
    p.add_argument("--aggression", type=int, default=5)
    p.add_argument("--risk", type=int, default=5)
    p.add_argument("--bio", type=str, default="")
    p.add_argument("--author", type=str, default="")
    p.add_argument("--output-dir", type=str, default="bots")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    """Execute the wizard command by delegating to wizard.main()."""
    argv: list[str] = []
    if args.non_interactive:
        argv.append("--non-interactive")
    if args.name:
        argv.extend(["--name", args.name])
    if args.emoji:
        argv.extend(["--emoji", args.emoji])
    if args.style:
        argv.extend(["--style", args.style])
    argv.extend(["--aggression", str(args.aggression)])
    argv.extend(["--risk", str(args.risk)])
    if args.bio:
        argv.extend(["--bio", args.bio])
    if args.author:
        argv.extend(["--author", args.author])
    argv.extend(["--output-dir", args.output_dir])

    from wizard import main as wizard_main

    wizard_main(argv)
