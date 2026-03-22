"""Callback registry — discover, validate, and execute bot callbacks.

Bot modules may define optional callback functions (setup, on_kill, react)
that are level-gated. This module introspects bot modules to find them,
validates they are callable, and provides a safe executor that never
crashes the match.
"""

from __future__ import annotations

import logging
import types
from dataclasses import dataclass
from typing import Any, Callable

__all__ = [
    "CALLBACK_NAMES",
    "CallbackSet",
    "discover_callbacks",
    "execute_callback",
]

logger = logging.getLogger(__name__)

CALLBACK_NAMES: tuple[str, ...] = ("setup", "on_kill", "react", "power_up", "evolve")


@dataclass
class CallbackSet:
    """Holds optional callback functions for a bot."""

    setup: Callable[..., Any] | None = None
    on_kill: Callable[..., Any] | None = None
    react: Callable[..., Any] | None = None
    power_up: Callable[..., Any] | None = None
    evolve: Callable[..., Any] | None = None


def discover_callbacks(
    module: types.ModuleType,
    unlocked_callbacks: set[str],
) -> CallbackSet:
    """Introspect a bot module for callback functions.

    Only returns callbacks that are both present on the module as callable
    attributes AND listed in *unlocked_callbacks* (level-gated).
    """
    found: dict[str, Callable[..., Any]] = {}
    for name in CALLBACK_NAMES:
        if name not in unlocked_callbacks:
            continue
        attr = getattr(module, name, None)
        if attr is not None and callable(attr):
            found[name] = attr
    return CallbackSet(**found)


def execute_callback(
    callback: Callable[..., Any] | None,
    *args: Any,
) -> None:
    """Safely execute a callback, catching any exception.

    Bot bugs should never crash the match. If the callback is None,
    this is a no-op.
    """
    if callback is None:
        return
    try:
        callback(*args)
    except Exception:
        logger.debug("Callback %s raised an exception", callback, exc_info=True)
