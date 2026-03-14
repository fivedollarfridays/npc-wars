"""Enemies wrapper class for bot authors.

No engine imports allowed — sandbox-safe.
"""

from __future__ import annotations

from npcwars._util import manhattan

__all__ = ["Enemies"]


class Enemies:
    """Wrapper around the enemies list for convenient filtering.

    Usage inside a decide() function::

        from npcwars.helpers import Me, Enemies

        def decide(state):
            me = Me(state)
            foes = Enemies(state)
            target = foes.closest()
            if target and me.dist_to(target) == 1:
                return me.attack(target)
    """

    __slots__ = ("_enemies", "_mx", "_my")

    def __init__(self, state: dict) -> None:
        self._enemies: list[dict] = state["enemies"]
        self._mx: int = state["me"]["x"]
        self._my: int = state["me"]["y"]

    @property
    def count(self) -> int:
        """Number of living enemies."""
        return len(self._enemies)

    def closest(self) -> dict | None:
        """Enemy with smallest manhattan distance, or None if empty."""
        if not self._enemies:
            return None
        return min(
            self._enemies,
            key=lambda e: manhattan(self._mx, self._my, e["x"], e["y"]),
        )

    def weakest(self) -> dict | None:
        """Enemy with lowest hp, or None if empty."""
        if not self._enemies:
            return None
        return min(self._enemies, key=lambda e: e["hp"])

    def wounded(self, threshold: int = 50) -> list[dict]:
        """Enemies with hp strictly below *threshold*."""
        return [e for e in self._enemies if e["hp"] < threshold]

    def adjacent(self) -> list[dict]:
        """Enemies at manhattan distance exactly 1."""
        return [
            e for e in self._enemies
            if manhattan(self._mx, self._my, e["x"], e["y"]) == 1
        ]

    def nearby(self, radius: int = 2) -> list[dict]:
        """Enemies within manhattan distance *radius* (inclusive)."""
        return [
            e for e in self._enemies
            if manhattan(self._mx, self._my, e["x"], e["y"]) <= radius
        ]
