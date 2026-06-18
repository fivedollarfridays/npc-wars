"""Bot-pool resolution for the balance harness (T74.1).

Two pools matter for the balance regression gate:

* ``bots`` — the repo-root ``bots/`` pool: the *real* equipped pool (14 bots
  including equipment loadouts and the locked-action bots Trapper/Viper/Mage),
  so equipment- and locked-action-related balance swings are actually caught.
* ``builtin`` — the shipped ``builtin_bots`` pool (6 bots, no equipment).
"""
from __future__ import annotations

from pathlib import Path

__all__ = ["builtin_bots_dir", "real_bots_dir", "resolve_pool"]

_CLI_DIR = Path(__file__).resolve().parent


def builtin_bots_dir() -> str:
    """Path to the shipped builtin bot pool (6 bots, no equipment)."""
    return str(_CLI_DIR.parent / "builtin_bots")


def real_bots_dir() -> str:
    """Path to the repo-root ``bots/`` pool — the real equipped pool (14 bots)."""
    return str(_CLI_DIR.parents[2] / "bots")


def resolve_pool(pool: str) -> str:
    """Resolve a ``--pool`` choice to a bots directory path."""
    return builtin_bots_dir() if pool == "builtin" else real_bots_dir()
