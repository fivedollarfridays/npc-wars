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
_BASE_HP = 50  # lowered; versatility bonus restores default to 145
_HP_PER_ARMOR = 0.8
_BASE_ENERGY = 80
_ENERGY_PER_MIND = 0.8
_MIN_DMG_SCALE = 0.6
_MAX_DMG_SCALE = 1.4
# Diminishing-return damage scales above baseline (power > 25)
_MIN_DMG_SCALE_HIGH = 0.3
_MAX_DMG_SCALE_HIGH = 0.8  # buffed from 0.6 — rewards Glass Cannon
_BASE_CRIT = 1.5
_CRIT_PER_POWER = 0.02
_DODGE_PER_SPEED = 0.3  # nerfed from 0.4 — dodge less dominant
# Accelerated dodge above baseline (speed > 25)
_DODGE_PER_SPEED_HIGH = 0.4  # nerfed from 1.0 — speed specialization less dominant
_DODGE_CAP = 20.0  # nerfed from 40.0 — hard cap on dodge
_DR_PER_ARMOR = 0.25  # buffed from 0.15 — rewards Tank builds
_DR_BASELINE = 25  # armor value that gives 0 DR
_REGEN_PER_MIND = 0.6  # buffed from 0.4 — rewards Mage builds
_REGEN_BASELINE = 25  # mind value that gives 0 regen

# Mind combat value (T74.3) — before this, mind only bought energy/regen, which
# is dead weight in a stats-only duel (the shared chase policy never rests/casts).
# The mage archetype (15/20/20/45) therefore lost ~87% of duels vs balanced and
# could not be tuned into the 40-60% band by any versatility constant.
# Mind above baseline (mind > 25) now grants a modest "battle-magic" combat
# contribution: a flat damage add (mind-fueled spell power) AND bonus effective
# HP (a mental barrier). Both use the (mind - 25) shape so the DEFAULT 25/25/25/25
# build and every sub-baseline build (mage's old fixtures all use mind<=25) are
# UNCHANGED — only genuinely mind-heavy builds (mind > 25) gain anything.
# Per-point values were tuned by the archetype duel sweep in
# tests/test_versatility_balance.py: at these constants mage reaches ~43% vs
# balanced (in band) while tank/bruiser/assassin stay in band and the full-pool
# balance report keeps the mind/Controller archetype under 2x uniform share.
# See docs/balance-mind-s74.md for the before/after duel matrix.
_MIND_BASELINE = 25  # mind value that gives 0 combat bonus
_DMG_PER_MIND = 0.8  # flat damage per mind point above baseline
_HP_PER_MIND = 2.5  # bonus effective HP per mind point above baseline

# Baseline values at power/speed = 25 (anchors for piecewise formulas)
_BASELINE_MIN_DMG = 15  # 25 * 0.6
_BASELINE_MAX_DMG = 35  # 25 * 1.4
_BASELINE_DODGE = 7.5  # 25 * 0.3

# Versatility bonus — rewards balanced stat distributions.
# Max bonus at 25/25/25/25 (variance=0), linearly decays with stat spread.
# Retuned in T73.6 (was 75/20): the old bonus made the 25/25/25/25 build
# strictly dominant (145 HP vs TankBot's 90). Measured archetype duels showed
# balanced winning 70-87% vs every specialist. New values put the three combat
# specialists (tank/bruiser/assassin) in a 40-50% balanced-win band while
# keeping versatility meaningful (balanced still gets +32 HP, +13 dmg).
# See docs/balance-versatility-s73.md for the measured matrix.
_VERSATILITY_HP_MAX = 32  # bonus HP for perfectly balanced build (retuned from 75)
_VERSATILITY_VARIANCE_CAP = 100.0  # variance at which bonus reaches 0 (unchanged)
_VERSATILITY_DMG_BONUS = 13  # flat damage bonus for balanced builds (retuned from 20)


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
    """Piecewise dodge: 0.3/pt below 25, 0.4/pt above 25."""
    if speed <= 25:
        return min(_DODGE_CAP, round(speed * _DODGE_PER_SPEED, 1))
    excess = speed - 25
    return min(_DODGE_CAP, round(_BASELINE_DODGE + excess * _DODGE_PER_SPEED_HIGH, 1))


def _calc_versatility_ratio(alloc: StatAllocation) -> float:
    """Return 1.0 for perfectly balanced, 0.0 for specialized builds."""
    mean = 25.0  # STAT_BUDGET / 4
    variance = sum(
        (v - mean) ** 2
        for v in (alloc.power, alloc.speed, alloc.armor, alloc.mind)
    ) / 4.0
    ratio = min(1.0, variance / _VERSATILITY_VARIANCE_CAP)
    return 1.0 - ratio


def calculate_derived(alloc: StatAllocation) -> DerivedStats:
    """Map raw stat allocation to gameplay values."""
    min_dmg, max_dmg = _calc_damage(alloc.power)
    v_ratio = _calc_versatility_ratio(alloc)
    bonus_hp = int(_VERSATILITY_HP_MAX * v_ratio)
    bonus_dmg = int(_VERSATILITY_DMG_BONUS * v_ratio)
    # Mind combat value (T74.3): only mind > 25 contributes; default unchanged.
    mind_excess = max(0, alloc.mind - _MIND_BASELINE)
    mind_dmg = int(mind_excess * _DMG_PER_MIND)
    mind_hp = int(mind_excess * _HP_PER_MIND)
    return DerivedStats(
        max_hp=int(_BASE_HP + alloc.armor * _HP_PER_ARMOR) + bonus_hp + mind_hp,
        max_energy=int(_BASE_ENERGY + alloc.mind * _ENERGY_PER_MIND),
        min_damage=min_dmg + bonus_dmg + mind_dmg,
        max_damage=max_dmg + bonus_dmg + mind_dmg,
        crit_multiplier=round(_BASE_CRIT + (alloc.power - 25) * _CRIT_PER_POWER, 2),
        dodge_chance=_calc_dodge(alloc.speed),
        initiative=alloc.speed,
        damage_reduction=max(0, int((alloc.armor - _DR_BASELINE) * _DR_PER_ARMOR)),
        energy_regen=max(0, int((alloc.mind - _REGEN_BASELINE) * _REGEN_PER_MIND)),
    )
