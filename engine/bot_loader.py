"""Compile submitted bot source into a runnable bot config.

Dep-light on purpose: this module imports only stdlib + engine.bot_scanner so
the Docker sandbox image can import it with just the ``engine/`` package
present (no ``server/`` / fastapi / redis). ``server.docker_sandbox``
re-exports ``load_bot_from_source`` from here for backward compatibility.
"""

from __future__ import annotations

import builtins as _builtins
from typing import Any

# Builtins the sandboxed bot source is allowed to reference. Anything not in
# this map (open, eval, __import__ of a blocked module, etc.) is unavailable.
_SAFE_BUILTIN_NAMES: tuple[str, ...] = (
    "abs", "all", "any", "bool", "dict", "enumerate",
    "float", "frozenset", "int", "len", "list", "max", "min",
    "print", "range", "round", "set", "sorted", "str", "sum",
    "tuple", "zip", "True", "False", "None",
    "isinstance", "issubclass", "hasattr", "hash", "id", "repr",
    "map", "filter", "reversed",
    "ValueError", "TypeError", "KeyError", "IndexError",
    "AttributeError", "StopIteration", "Exception",
)


def _build_safe_builtins() -> dict[str, Any]:
    """Return the restricted ``__builtins__`` mapping for bot execution."""
    from engine.bot_scanner import BLOCKED_MODULES

    safe = {
        name: getattr(_builtins, name)
        for name in _SAFE_BUILTIN_NAMES
        if hasattr(_builtins, name)
    }
    real_import = _builtins.__import__

    def _restricted_import(name: str, *args: Any, **kwargs: Any) -> Any:
        root = name.split(".")[0]
        if root in BLOCKED_MODULES:
            raise ImportError(f"Import blocked: '{name}'")
        return real_import(name, *args, **kwargs)

    safe["__import__"] = _restricted_import
    return safe


def load_bot_from_source(source: str, label: str) -> dict[str, Any]:
    """Exec bot source code and return a bot config dict.

    Source is pre-scanned for security violations before execution.
    Raises ValueError if scan fails or required attributes are missing.
    """
    from engine.bot_scanner import scan_bot_source

    errors = scan_bot_source(source)
    if errors:
        raise ValueError(f"Bot '{label}' failed scan: {'; '.join(errors[:3])}")

    namespace: dict[str, Any] = {"__builtins__": _build_safe_builtins()}
    exec(compile(source, f"<{label}>", "exec"), namespace)  # noqa: S102

    name = namespace.get("BOT_NAME")
    emoji = namespace.get("BOT_EMOJI")
    decide = namespace.get("decide")

    if not name or not emoji or not callable(decide):
        raise ValueError(
            f"Bot source '{label}' missing required attributes "
            "(BOT_NAME, BOT_EMOJI, decide)"
        )

    return {
        "name": name,
        "emoji": emoji,
        "bio": namespace.get("BOT_BIO", ""),
        "author": namespace.get("BOT_AUTHOR", "unknown"),
        "decide_func": decide,
    }
