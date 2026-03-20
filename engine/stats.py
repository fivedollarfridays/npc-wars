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
_BASE_HP = 55  # lowered from 80; versatility bonus restores default to 100
_HP_PER_ARMOR = 0.8
_BASE_ENERGY = 80
_ENERGY_PER_MIND = 0.8
_MIN_DMG_SCALE = 0.6
_MAX_DMG_SCALE = 1.4
# Diminishing-return damage scales above baseline (power > 25)
_MIN_DMG_SCALE_HIGH = 0.3
_MAX_DMG_SCALE_HIGH = 0.6
_BASE_CRIT = 1.5
_CRIT_PER_POWER = 0.02
_DODGE_PER_SPEED = 0.4
# Accelerated dodge above baseline (speed > 25)
_DODGE_PER_SPEED_HIGH = 1.0
_DODGE_CAP = 40.0
_DR_PER_ARMOR = 0.15  # was 0.3 — reduced to weaken armor-heavy builds
_DR_BASELINE = 25  # armor value that gives 0 DR
_REGEN_PER_MIND = 0.4  # was 0.2 — boosted to reward mind investment
_REGEN_BASELINE = 25  # mind value that gives 0 regen

# Baseline values at power/speed = 25 (anchors for piecewise formulas)
_BASELINE_MIN_DMG = 15  # 25 * 0.6
_BASELINE_MAX_DMG = 35  # 25 * 1.4
_BASELINE_DODGE = 10.0  # 25 * 0.4

# Versatility bonus — rewards balanced stat distributions.
# Max bonus at 25/25/25/25 (variance=0), linearly decays with stat spread.
_VERSATILITY_HP_MAX = 25  # bonus HP for perfectly balanced build
_VERSATILITY_VARIANCE_CAP = 200.0  # variance at which bonus reaches 0


def _calc_damage(power: int) -> tuple[int, int]:
    """Piecewise damage: linear below 25, diminishing above."""
    if power <= 25:
        return max(1, int(power * _MIN_DMG_SCALE)), int(power * _MAX_DMG_SCALE)
    excess = power - 25
    return (
        max(1, int(_BASELINE_MIN_DMG + excess * _MIN_DMG_SCALE_HIGH)),
        int(_BASELINE_MAX_DMG + excess * _MAX_DMG_SCALE_HIGH),
    )


def _calc_dodge(speed: int) -> float:
    """Piecewise dodge: 0.4/pt below 25, 1.0/pt above 25."""
    if speed <= 25:
        return min(_DODGE_CAP, round(speed * _DODGE_PER_SPEED, 1))
    excess = speed - 25
    return min(_DODGE_CAP, round(_BASELINE_DODGE + excess * _DODGE_PER_SPEED_HIGH, 1))


def _calc_versatility_hp(alloc: StatAllocation) -> int:
    """Bonus HP for balanced stat distributions (low variance)."""
    mean = 25.0  # STAT_BUDGET / 4
    variance = sum(
        (v - mean) ** 2
        for v in (alloc.power, alloc.speed, alloc.armor, alloc.mind)
    ) / 4.0
    ratio = min(1.0, variance / _VERSATILITY_VARIANCE_CAP)
    return int(_VERSATILITY_HP_MAX * (1.0 - ratio))


def calculate_derived(alloc: StatAllocation) -> DerivedStats:
    """Map raw stat allocation to gameplay values."""
    min_dmg, max_dmg = _calc_damage(alloc.power)
    bonus_hp = _calc_versatility_hp(alloc)
    return DerivedStats(
        max_hp=int(_BASE_HP + alloc.armor * _HP_PER_ARMOR) + bonus_hp,
        max_energy=int(_BASE_ENERGY + alloc.mind * _ENERGY_PER_MIND),
        min_damage=min_dmg,
        max_damage=max_dmg,
        crit_multiplier=round(_BASE_CRIT + (alloc.power - 25) * _CRIT_PER_POWER, 2),
        dodge_chance=_calc_dodge(alloc.speed),
        initiative=alloc.speed,
        damage_reduction=max(0, int((alloc.armor - _DR_BASELINE) * _DR_PER_ARMOR)),
        energy_regen=max(0, int((alloc.mind - _REGEN_BASELINE) * _REGEN_PER_MIND)),
    )
