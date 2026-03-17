"""Built-in bot files shipped with the npcwars package."""
from __future__ import annotations

import importlib.resources

__all__ = ["BUILTIN_NAMES", "list_builtin_bots", "get_bot_source"]

BUILTIN_NAMES: tuple[str, ...] = (
    "example_aggro",
    "example_tank",
    "example_kiter",
    "example_random",
    "example_vibes",
    "starter",
    "template",
)


def list_builtin_bots() -> list[str]:
    """Return names of all built-in bots."""
    return list(BUILTIN_NAMES)


def get_bot_source(name: str) -> str:
    """Return the source code of a built-in bot by name."""
    if name not in BUILTIN_NAMES:
        raise ValueError(
            f"Unknown built-in bot: {name!r}. Available: {BUILTIN_NAMES!r}"
        )
    ref = importlib.resources.files("npcwars.builtin_bots").joinpath(f"{name}.py")
    return ref.read_text(encoding="utf-8")
