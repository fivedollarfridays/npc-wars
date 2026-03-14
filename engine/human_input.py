"""Human input adapters for copilot mode.

Defines an abstract interface for human input sources and concrete
implementations for testing (MockInputAdapter) and local keyboard
input (LocalInputAdapter).
"""

from abc import ABC, abstractmethod
from typing import Any

__all__ = ["HumanInputAdapter", "MockInputAdapter", "LocalInputAdapter"]


class HumanInputAdapter(ABC):
    """Abstract base for human input sources.

    The engine calls ``get_action`` each round when a human player is
    attached.  Returning ``None`` signals timeout — the bot's own
    ``decide()`` function is used as fallback.
    """

    @abstractmethod
    def get_action(
        self, state: dict[str, Any], timeout_s: float,
    ) -> tuple[str, ...] | None:
        """Collect a human action within *timeout_s* seconds.

        Args:
            state: The same state dict the bot's decide() receives.
            timeout_s: Maximum seconds to wait for input.

        Returns:
            An action tuple like ``("move", "east")`` or ``None`` on timeout.
        """

    async def get_action_async(
        self, state: dict[str, Any], timeout_s: float,
    ) -> tuple[str, ...] | None:
        """Async version of get_action. Default delegates to sync version.

        Subclasses may override for true async I/O (e.g. WebSocket).
        """
        return self.get_action(state, timeout_s)


class MockInputAdapter(HumanInputAdapter):
    """Returns pre-configured actions in sequence. For testing."""

    def __init__(self, actions: list[tuple[str, ...] | None]) -> None:
        self._actions = list(actions)
        self._index = 0

    def get_action(
        self, state: dict[str, Any], timeout_s: float,
    ) -> tuple[str, ...] | None:
        if self._index >= len(self._actions):
            return None
        action = self._actions[self._index]
        self._index += 1
        return action


class LocalInputAdapter(HumanInputAdapter):
    """Reads keyboard input with a timeout for local play.

    Uses ``select.select`` on stdin — Unix/macOS only. Not supported on
    Windows (``select`` does not work on stdin file descriptors there).

    Maps keys to actions:
        Arrow keys -> move directions
        W/A/S/D   -> attack directions
        R         -> rest
        F         -> defend
    """

    _KEY_MAP: dict[str, tuple[str, ...]] = {
        "up": ("move", "north"),
        "down": ("move", "south"),
        "left": ("move", "west"),
        "right": ("move", "east"),
        "w": ("attack", "north"),
        "s": ("attack", "south"),
        "a": ("attack", "west"),
        "d": ("attack", "east"),
        "r": ("rest",),
        "f": ("defend",),
    }

    def get_action(
        self, state: dict[str, Any], timeout_s: float,
    ) -> tuple[str, ...] | None:
        """Read a single keypress within timeout. Returns None on timeout."""
        import select
        import sys

        ready, _, _ = select.select([sys.stdin], [], [], timeout_s)
        if not ready:
            return None
        key = sys.stdin.readline().strip().lower()
        return self._KEY_MAP.get(key)
