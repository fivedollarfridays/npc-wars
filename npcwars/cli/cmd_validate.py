"""npcwars validate -- validate bot files."""
from __future__ import annotations

import argparse
import sys

__all__ = ["register", "run"]


def register(subparser: argparse._SubParsersAction) -> None:
    """Register the validate subcommand."""
    p = subparser.add_parser("validate", help="Validate bot files")
    p.add_argument("paths", nargs="+", help="Bot file path(s) to validate")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    """Execute the validate command."""
    from scripts.validate_bot import validate_bot

    all_ok = True
    for path in args.paths:
        ok, errors = validate_bot(path)
        if ok:
            print(f"  PASS  {path}")
        else:
            print(f"  FAIL  {path}")
            for e in errors:
                print(f"        {e}")
            all_ok = False

    if not all_ok:
        sys.exit(1)
