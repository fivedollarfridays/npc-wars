"""Stat allocation system — budget-constrained bot stat distribution."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "STAT_BUDGET",
    "STAT_MIN",
    "STAT_MAX",
    "StatAllocation",
    "DEFAULT_ALLOCATION",
    "validate_allocation",
    "DerivedStats",
    "calculate_derived",
]

STAT_BUDGET: int = 100
STAT_MIN: int = 5
STAT_MAX: int = 80


@dataclass(frozen=True, slots=True)
class StatAllocation:
    """Immutable stat allocation with four slots."""

    power: int
    speed: int
    armor: int
    mind: int


DEFAULT_ALLOCATION = StatAllocation(25, 25, 25, 25)


def validate_allocation(
    power: int, speed: int, armor: int, mind: int
) -> StatAllocation:
    """Validate and return a frozen StatAllocation.

    Raises ValueError if:
    - sum of stats != STAT_BUDGET (100)
    - any stat < STAT_MIN (5)
    - any stat > STAT_MAX (80)
    """
    stats = {"power": power, "speed": speed, "armor": armor, "mind": mind}

    for name, value in stats.items():
        if value < STAT_MIN:
            msg = f"{name}={value} below minimum {STAT_MIN}"
            raise ValueError(msg)
        if value > STAT_MAX:
            msg = f"{name}={value} above maximum {STAT_MAX}"
            raise ValueError(msg)

    total = sum(stats.values())
    if total != STAT_BUDGET:
        msg = f"Stat total {total} must equal {STAT_BUDGET}"
        raise ValueError(msg)

    return StatAllocation(power=power, speed=speed, armor=armor, mind=mind)


@dataclass(frozen=True, slots=True)
class DerivedStats:
    """Gameplay values derived from a stat allocation."""

    max_hp: int
    max_energy: int
    min_damage: int
    max_damage: int
    crit_multiplier: float
    dodge_chance: float
    initiative: int
    damage_reduction: int
    energy_regen: int


def calculate_derived(alloc: StatAllocation) -> DerivedStats:
    """Map raw stat allocation to gameplay values.

    Formulas are calibrated so DEFAULT_ALLOCATION (25/25/25/25) produces
    exactly the pre-overhaul game constants.
    """
    return DerivedStats(
        max_hp=int(80 + alloc.armor * 0.8),
        max_energy=int(80 + alloc.mind * 0.8),
        min_damage=max(1, int(alloc.power * 0.6)),
        max_damage=int(alloc.power * 1.4),
        crit_multiplier=round(1.5 + (alloc.power - 25) * 0.02, 2),
        dodge_chance=min(40.0, round(alloc.speed * 0.4, 1)),
        initiative=alloc.speed,
        damage_reduction=max(0, int((alloc.armor - 25) * 0.3)),
        energy_regen=max(0, int((alloc.mind - 25) * 0.2)),
    )
