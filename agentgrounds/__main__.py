"""Support ``python -m agentgrounds``."""
from __future__ import annotations

import sys

GAMES = {
    "killswitch": "agentgrounds.wars.cli",
    "circuit": "agentgrounds.circuit.cli",
    "wars": "agentgrounds.wars.cli",  # backward compat alias
}


def main(argv: list[str] | None = None) -> None:
    """Platform CLI dispatcher: routes ``agentgrounds <game> ...`` to the game subpackage."""
    args = argv if argv is not None else sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        _print_help()
        sys.exit(0 if args else 2)

    if args[0] in ("--version", "-V"):
        _print_version()
        sys.exit(0)

    game = args[0]
    if game not in GAMES:
        print(f"Unknown game: {game!r}")
        _print_help()
        sys.exit(2)

    _dispatch(game, args[1:])


def _print_help() -> None:
    """Print platform help listing available games."""
    print("Agent Grounds -- competitive bot arena platform")
    print()
    print("Usage: agentgrounds <game> [subcommand] [options]")
    print()
    print("Available games:")
    for name in sorted(GAMES):
        label = " (alias for killswitch)" if name == "wars" else ""
        print(f"  {name}{label}")
    print()
    print("Examples:")
    print("  agentgrounds killswitch play --seed 42")
    print("  agentgrounds circuit race --laps 10")
    print("  agentgrounds killswitch watch results/match_001.json")


def _print_version() -> None:
    """Print the platform version."""
    try:
        from importlib.metadata import version

        ver = version("agent-grounds")
    except Exception:
        ver = "dev"
    print(f"agentgrounds {ver}")


def _dispatch(game: str, args: list[str]) -> None:
    """Route to the game's CLI main function."""
    import importlib

    module = importlib.import_module(GAMES[game])
    module.main(args)


if __name__ == "__main__":
    main()
