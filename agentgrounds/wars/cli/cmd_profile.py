"""agentgrounds wars profile -- view player profiles and leaderboard."""
from __future__ import annotations

import argparse

from engine.profile_db import DEFAULT_DB_PATH, get_leaderboard, get_profile, init_profile_db
from engine.profile_display import format_leaderboard, format_profile

__all__ = ["register", "run"]


def register(subparser: argparse._SubParsersAction) -> None:
    """Register the profile subcommand."""
    p = subparser.add_parser("profile", help="View player profile or leaderboard")
    p.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Player name (omit for leaderboard)",
    )
    p.add_argument(
        "--db-path",
        type=str,
        default=DEFAULT_DB_PATH,
        help="Path to profiles database",
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    """Execute the profile command."""
    conn = init_profile_db(args.db_path)
    try:
        if args.name:
            profile = get_profile(conn, args.name)
            if profile is None:
                print(f"No profile found for '{args.name}'.")
                return
            print(format_profile(profile))
        else:
            profiles = get_leaderboard(conn, limit=10)
            if not profiles:
                print("No profiles found.")
                return
            print(format_leaderboard(profiles))
    finally:
        conn.close()
