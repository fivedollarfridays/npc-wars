"""agentgrounds wars leaderboard — show player rankings."""
from __future__ import annotations

import argparse
import json
import sys
from urllib.error import URLError
from urllib.request import Request, urlopen

__all__ = ["register", "run"]

_DEFAULT_SERVER = "http://localhost:8000"


def register(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("leaderboard", help="Show player rankings")
    p.add_argument("--sort", type=str, default="wins",
                   choices=["wins", "kills", "win_rate"],
                   help="Sort by (default: wins)")
    p.add_argument("--server", type=str, default=None, help="Server URL")
    p.add_argument("--local", action="store_true", help="Use local profile DB")
    p.add_argument("--limit", type=int, default=20, help="Number of results")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    if args.local:
        _show_local(args.limit)
        return

    server = args.server or _load_server_url()
    try:
        _show_remote(server, args.sort, args.limit)
    except (URLError, OSError) as e:
        print(f"Server unavailable ({e}), falling back to local...", file=sys.stderr)
        _show_local(args.limit)


def _show_remote(server: str, sort_by: str, limit: int) -> None:
    url = f"{server}/api/leaderboard?sort_by={sort_by}&limit={limit}"
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())

    if not data:
        print("No players yet.")
        return

    print(f"\n{'#':>3}  {'Name':<20} {'Wins':>6} {'Win%':>6} {'Kills':>6} {'Level':>6}")
    print("-" * 55)
    for i, p in enumerate(data[:limit], 1):
        name = p.get("name", "?")[:20]
        wins = p.get("wins", 0)
        rate = p.get("win_rate", 0)
        kills = p.get("kills", 0)
        level = p.get("level", 1)
        print(f"{i:>3}  {name:<20} {wins:>6} {rate:>5.1f}% {kills:>6} {level:>6}")
    print()


def _show_local(limit: int) -> None:
    try:
        from engine.profile_db import get_leaderboard, init_profile_db
        conn = init_profile_db()
        profiles = get_leaderboard(conn, limit=limit)
        conn.close()
    except Exception:
        print("No local profile data available.")
        return

    if not profiles:
        print("No local profiles yet.")
        return

    print(f"\n{'#':>3}  {'Name':<20} {'Wins':>6} {'Matches':>8} {'Kills':>6} {'Level':>6}")
    print("-" * 58)
    for i, p in enumerate(profiles[:limit], 1):
        name = str(p.get("name", "?"))[:20]
        print(f"{i:>3}  {name:<20} {p.get('wins', 0):>6} {p.get('matches', 0):>8} "
              f"{p.get('kills', 0):>6} {p.get('level', 1):>6}")
    print()


def _load_server_url() -> str:
    from pathlib import Path
    config_file = Path.home() / ".agentgrounds" / "config.json"
    if config_file.exists():
        data = json.loads(config_file.read_text())
        return data.get("server", _DEFAULT_SERVER)
    return _DEFAULT_SERVER
