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


# Scaling coefficients — tuned so DEFAULT_ALLOCATION (25/25/25/25)
# produces the pre-overhaul constants (HP=100, energy=100, damage=25, etc.)
_BASE_HP = 80
_HP_PER_ARMOR = 0.8
_BASE_ENERGY = 80
_ENERGY_PER_MIND = 0.8
_MIN_DMG_SCALE = 0.6
_MAX_DMG_SCALE = 1.4
_BASE_CRIT = 1.5
_CRIT_PER_POWER = 0.02
_DODGE_PER_SPEED = 0.4
_DODGE_CAP = 40.0
_DR_PER_ARMOR = 0.3
_DR_BASELINE = 25  # armor value that gives 0 DR
_REGEN_PER_MIND = 0.2
_REGEN_BASELINE = 25  # mind value that gives 0 regen


def calculate_derived(alloc: StatAllocation) -> DerivedStats:
    """Map raw stat allocation to gameplay values."""
    return DerivedStats(
        max_hp=int(_BASE_HP + alloc.armor * _HP_PER_ARMOR),
        max_energy=int(_BASE_ENERGY + alloc.mind * _ENERGY_PER_MIND),
        min_damage=max(1, int(alloc.power * _MIN_DMG_SCALE)),
        max_damage=int(alloc.power * _MAX_DMG_SCALE),
        crit_multiplier=round(_BASE_CRIT + (alloc.power - 25) * _CRIT_PER_POWER, 2),
        dodge_chance=min(_DODGE_CAP, round(alloc.speed * _DODGE_PER_SPEED, 1)),
        initiative=alloc.speed,
        damage_reduction=max(0, int((alloc.armor - _DR_BASELINE) * _DR_PER_ARMOR)),
        energy_regen=max(0, int((alloc.mind - _REGEN_BASELINE) * _REGEN_PER_MIND)),
    )
