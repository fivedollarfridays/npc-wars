"""Me wrapper class for bot authors.

No engine imports allowed — sandbox-safe.
"""

from __future__ import annotations

from agentgrounds.wars._util import OPPOSITE, direction_toward, manhattan, unpack_target

__all__ = ["Me"]


class Me:
    """Convenience wrapper around the state dict for bot authors.

    Usage inside a decide() function::

        from agentgrounds.wars.helpers import Me

        def decide(state):
            me = Me(state)
            if me.hp < 30:
                return me.flee_storm()
            ...
    """

    __slots__ = (
        "x", "y", "hp", "energy", "attack_power", "defense",
        "grid_size", "storm_border", "round", "_enemies",
    )

    def __init__(self, state: dict) -> None:
        me = state["me"]
        self.x: int = me["x"]
        self.y: int = me["y"]
        self.hp: int = me["hp"]
        self.energy: int = me["energy"]
        self.attack_power: int = me["attack_power"]
        self.defense: int = me["defense"]
        self.grid_size: int = state["grid_size"]
        self.storm_border: int = state["storm_border"]
        self.round: int = state["round"]
        self._enemies: list[dict] = state["enemies"]

    # --- actions ---

    def rest(self) -> tuple[str]:
        """Return a rest action tuple."""
        return ("rest",)

    def defend(self) -> tuple[str]:
        """Return a defend action tuple."""
        return ("defend",)

    def flee_storm(self) -> tuple[str, str]:
        """Move toward the grid center to escape the storm."""
        return self.move_toward_center()

    def move_toward_center(self) -> tuple[str, str]:
        """Move toward the center of the grid."""
        cx = self.grid_size // 2
        cy = self.grid_size // 2
        return ("move", direction_toward(self.x, self.y, cx, cy))

    def move_toward(self, target: dict | tuple) -> tuple[str, str]:
        """Move toward *target* (enemy dict or (x, y) tuple)."""
        tx, ty = unpack_target(target)
        return ("move", direction_toward(self.x, self.y, tx, ty))

    def move_away_from(self, target: dict | tuple) -> tuple[str, str]:
        """Move in the opposite direction of *target*."""
        tx, ty = unpack_target(target)
        d = direction_toward(self.x, self.y, tx, ty)
        return ("move", OPPOSITE[d])

    # --- combat awareness ---

    def dist_to(self, target: dict | tuple) -> int:
        """Manhattan distance to *target* (enemy dict or (x, y) tuple)."""
        tx, ty = unpack_target(target)
        return manhattan(self.x, self.y, tx, ty)

    def attack(self, enemy: dict) -> tuple[str, str]:
        """Return an attack action toward *enemy*."""
        return ("attack", direction_toward(self.x, self.y, enemy["x"], enemy["y"]))

    def adjacent_enemies(self) -> list[dict]:
        """Return enemies at manhattan distance exactly 1."""
        return [e for e in self._enemies if self.dist_to(e) == 1]

    def nearby_enemies(self, radius: int = 2) -> list[dict]:
        """Return enemies within manhattan distance <= *radius*."""
        return [e for e in self._enemies if self.dist_to(e) <= radius]

    def can_kill_adjacent(self) -> bool:
        """True if any adjacent enemy has hp <= self.attack_power."""
        return any(e["hp"] <= self.attack_power for e in self.adjacent_enemies())

    def weakest_adjacent(self) -> dict | None:
        """Return the lowest-hp adjacent enemy, or None."""
        adj = self.adjacent_enemies()
        if not adj:
            return None
        return min(adj, key=lambda e: e["hp"])

    def threatened(self) -> bool:
        """True if adjacent enemies exist AND (hp < 40 OR outnumbered)."""
        adj = self.adjacent_enemies()
        if not adj:
            return False
        return self.hp < 40 or len(adj) > 1
