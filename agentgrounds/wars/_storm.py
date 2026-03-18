"""Storm wrapper class for bot authors.

No engine imports allowed — sandbox-safe.
"""

from __future__ import annotations

from agentgrounds.wars._util import is_in_storm

__all__ = ["Storm"]


class Storm:
    """Convenience wrapper for storm state.

    Usage inside a decide() function::

        from agentgrounds.wars.helpers import Storm

        def decide(state):
            storm = Storm(state)
            if storm.danger:
                return ("move", "north")  # flee!
    """

    __slots__ = ("_x", "_y", "_grid_size", "_storm_border")

    def __init__(self, state: dict) -> None:
        me = state["me"]
        self._x: int = me["x"]
        self._y: int = me["y"]
        self._grid_size: int = state["grid_size"]
        self._storm_border: int = state["storm_border"]

    @property
    def active(self) -> bool:
        """True when the storm is closing in (storm_border > 0)."""
        return self._storm_border > 0

    @property
    def danger(self) -> bool:
        """True when the bot is in the storm or within 1 tile of it."""
        return is_in_storm(
            self._x, self._y, self._grid_size, self._storm_border,
        ) or (
            self._storm_border > 0
            and is_in_storm(
                self._x, self._y, self._grid_size, self._storm_border + 1,
            )
        )

    @property
    def border(self) -> int:
        """Raw storm_border value."""
        return self._storm_border

    def safe_zone_center(self) -> tuple[int, int]:
        """Return the center of the safe zone."""
        return (self._grid_size // 2, self._grid_size // 2)
