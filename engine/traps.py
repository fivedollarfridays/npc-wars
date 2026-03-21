"""Trap action system — place hidden traps that trigger on enemy movement."""

from __future__ import annotations

from dataclasses import dataclass

# --- Constants ---
TRAP_BASE_DAMAGE = 20
TRAP_POWER_SCALE = 0.5
TRAP_POWER_BASELINE = 25
TRAP_LIFETIME = 10
TRAP_COOLDOWN = 3


@dataclass(frozen=True)
class Trap:
    """An active trap on the grid."""

    owner_emoji: str
    x: int
    y: int
    damage: float
    placed_round: int
    expires_round: int


def calculate_trap_damage(power: int) -> float:
    """Calculate trap damage scaled by POWER stat.

    Formula: TRAP_BASE_DAMAGE + TRAP_POWER_SCALE * max(0, power - TRAP_POWER_BASELINE)
    """
    return TRAP_BASE_DAMAGE + TRAP_POWER_SCALE * max(0, power - TRAP_POWER_BASELINE)


class TrapManager:
    """Manages trap placement, triggering, expiry, and cleanup."""

    def __init__(self) -> None:
        self._traps: dict[str, list[Trap]] = {}
        self._last_placed: dict[str, int] = {}  # emoji -> round of last placement

    def place_trap(
        self, owner_emoji: str, x: int, y: int, power: int, round_num: int,
    ) -> Trap | None:
        """Place a trap at (x, y). Returns Trap or None if cooldown blocked."""
        next_allowed = self._last_placed.get(owner_emoji, 0) + TRAP_COOLDOWN
        if owner_emoji in self._last_placed and round_num < next_allowed:
            return None

        damage = calculate_trap_damage(power)
        trap = Trap(
            owner_emoji=owner_emoji,
            x=x, y=y,
            damage=damage,
            placed_round=round_num,
            expires_round=round_num + TRAP_LIFETIME,
        )
        self._traps.setdefault(owner_emoji, []).append(trap)
        self._last_placed[owner_emoji] = round_num
        return trap

    def get_traps_for(self, emoji: str) -> list[Trap]:
        """Return active traps owned by the given bot."""
        return list(self._traps.get(emoji, []))

    def get_all_traps(self) -> list[Trap]:
        """Return all active traps across all owners."""
        result: list[Trap] = []
        for traps in self._traps.values():
            result.extend(traps)
        return result

    def check_triggers(
        self, victim_emoji: str, x: int, y: int, round_num: int,
    ) -> list[Trap]:
        """Find enemy traps at position, remove and return triggered traps."""
        triggered: list[Trap] = []
        for owner, traps in self._traps.items():
            if owner == victim_emoji:
                continue
            remaining: list[Trap] = []
            for trap in traps:
                if trap.x == x and trap.y == y:
                    triggered.append(trap)
                else:
                    remaining.append(trap)
            self._traps[owner] = remaining
        return triggered

    def expire_traps(self, round_num: int) -> list[Trap]:
        """Remove expired traps, return them."""
        expired: list[Trap] = []
        for owner in list(self._traps):
            remaining: list[Trap] = []
            for trap in self._traps[owner]:
                if trap.expires_round <= round_num:
                    expired.append(trap)
                else:
                    remaining.append(trap)
            self._traps[owner] = remaining
        return expired

    def remove_bot_traps(self, emoji: str) -> list[Trap]:
        """Remove all traps for a dead bot, return them."""
        removed = self._traps.pop(emoji, [])
        return removed

    def get_cooldown_at(self, emoji: str, current_round: int) -> int:
        """Rounds remaining until bot can place next trap at given round."""
        if emoji not in self._last_placed:
            return 0
        next_allowed = self._last_placed[emoji] + TRAP_COOLDOWN
        return max(0, next_allowed - current_round)


__all__ = [
    "TRAP_BASE_DAMAGE",
    "TRAP_POWER_SCALE",
    "TRAP_POWER_BASELINE",
    "TRAP_LIFETIME",
    "TRAP_COOLDOWN",
    "Trap",
    "TrapManager",
    "calculate_trap_damage",
]
