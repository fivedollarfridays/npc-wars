"""Tests for engine.stats — stat allocation dataclass and validation."""

from __future__ import annotations

import pytest

from engine.stats import (
    DEFAULT_ALLOCATION,
    STAT_BUDGET,
    STAT_MAX,
    STAT_MIN,
    DerivedStats,
    StatAllocation,
    calculate_derived,
    validate_allocation,
)


# --- StatAllocation dataclass ---


def test_default_allocation_values() -> None:
    """DEFAULT_ALLOCATION is (25, 25, 25, 25)."""
    assert DEFAULT_ALLOCATION.power == 25
    assert DEFAULT_ALLOCATION.speed == 25
    assert DEFAULT_ALLOCATION.armor == 25
    assert DEFAULT_ALLOCATION.mind == 25


def test_stat_allocation_is_frozen() -> None:
    """Cannot set attributes on StatAllocation instance."""
    alloc = StatAllocation(25, 25, 25, 25)
    with pytest.raises(AttributeError):
        alloc.power = 50  # type: ignore[misc]


def test_stat_allocation_has_slots() -> None:
    """StatAllocation uses __slots__."""
    alloc = StatAllocation(25, 25, 25, 25)
    assert not hasattr(alloc, "__dict__")


# --- validate_allocation: valid inputs ---


def test_validate_default_passes() -> None:
    """validate_allocation(25, 25, 25, 25) succeeds."""
    result = validate_allocation(25, 25, 25, 25)
    assert isinstance(result, StatAllocation)
    assert result.power == 25


def test_validate_asymmetric_passes() -> None:
    """validate_allocation(50, 20, 15, 15) succeeds."""
    result = validate_allocation(50, 20, 15, 15)
    assert result.power == 50
    assert result.speed == 20
    assert result.armor == 15
    assert result.mind == 15


def test_validate_extreme_passes() -> None:
    """validate_allocation(80, 5, 10, 5) succeeds."""
    result = validate_allocation(80, 5, 10, 5)
    assert result.power == 80
    assert result.speed == 5


# --- validate_allocation: invalid inputs ---


def test_validate_sum_too_low() -> None:
    """validate_allocation(20, 20, 20, 20) raises ValueError."""
    with pytest.raises(ValueError, match="must equal"):
        validate_allocation(20, 20, 20, 20)


def test_validate_sum_too_high() -> None:
    """validate_allocation(30, 30, 30, 30) raises ValueError."""
    with pytest.raises(ValueError, match="must equal"):
        validate_allocation(30, 30, 30, 30)


def test_validate_stat_below_min() -> None:
    """validate_allocation(4, 32, 32, 32) raises ValueError."""
    with pytest.raises(ValueError, match="below minimum"):
        validate_allocation(4, 32, 32, 32)


def test_validate_stat_above_max() -> None:
    """validate_allocation(81, 5, 9, 5) raises ValueError."""
    with pytest.raises(ValueError, match="above maximum"):
        validate_allocation(81, 5, 9, 5)


def test_validate_all_at_min() -> None:
    """validate_allocation(5, 5, 5, 85) raises ValueError (85 > MAX)."""
    with pytest.raises(ValueError, match="above maximum"):
        validate_allocation(5, 5, 5, 85)


# --- Constants ---


def test_constants_values() -> None:
    """Verify constant values are as specified."""
    assert STAT_BUDGET == 100
    assert STAT_MIN == 5
    assert STAT_MAX == 80


# --- DerivedStats: default allocation (25/25/25/25) must match current game ---


def test_derived_default_max_hp() -> None:
    """Default allocation → max_hp == 102 (50 base + 20 armor + 32 versatility)."""
    ds = calculate_derived(DEFAULT_ALLOCATION)
    assert ds.max_hp == 102


def test_derived_default_max_energy() -> None:
    """Default allocation → max_energy == 100 (current STARTING_ENERGY)."""
    ds = calculate_derived(DEFAULT_ALLOCATION)
    assert ds.max_energy == 100


def test_derived_default_damage_range() -> None:
    """Default allocation → min_damage == 28, max_damage == 48 (with versatility bonus)."""
    ds = calculate_derived(DEFAULT_ALLOCATION)
    assert ds.min_damage == 28
    assert ds.max_damage == 48


def test_derived_default_crit() -> None:
    """Default allocation → crit_multiplier == 1.5."""
    ds = calculate_derived(DEFAULT_ALLOCATION)
    assert ds.crit_multiplier == 1.5


def test_derived_default_dodge() -> None:
    """Default allocation → dodge_chance == 7.5 percent."""
    ds = calculate_derived(DEFAULT_ALLOCATION)
    assert ds.dodge_chance == 7.5


def test_derived_default_initiative() -> None:
    """Default allocation → initiative == 25."""
    ds = calculate_derived(DEFAULT_ALLOCATION)
    assert ds.initiative == 25


def test_derived_default_dr() -> None:
    """Default allocation → damage_reduction == 0."""
    ds = calculate_derived(DEFAULT_ALLOCATION)
    assert ds.damage_reduction == 0


def test_derived_default_energy_regen() -> None:
    """Default allocation → energy_regen == 0."""
    ds = calculate_derived(DEFAULT_ALLOCATION)
    assert ds.energy_regen == 0


# --- DerivedStats: non-default allocations ---


def test_derived_high_armor_hp() -> None:
    """High armor (50) → max_hp == 90 (specialist, no versatility bonus)."""
    ds = calculate_derived(StatAllocation(15, 15, 50, 20))
    assert ds.max_hp == 90


def test_derived_high_armor_dr() -> None:
    """High armor (50) → damage_reduction == 6 (buffed DR scaling)."""
    ds = calculate_derived(StatAllocation(15, 15, 50, 20))
    assert ds.damage_reduction == 6


def test_derived_high_power_damage() -> None:
    """High power (50) → diminishing returns: min=22, max=55 (specialist, no versatility)."""
    ds = calculate_derived(StatAllocation(50, 15, 15, 20))
    assert ds.min_damage == 22
    assert ds.max_damage == 55


def test_derived_high_speed_dodge() -> None:
    """High speed (50) → boosted dodge: 17.5% (nerfed scaling)."""
    ds = calculate_derived(StatAllocation(15, 50, 15, 20))
    assert ds.dodge_chance == 17.5


def test_derived_high_mind_energy() -> None:
    """High mind (50) → max_energy == 120."""
    ds = calculate_derived(StatAllocation(15, 15, 20, 50))
    assert ds.max_energy == 120


def test_derived_high_mind_regen() -> None:
    """High mind (50) → energy_regen == 15 (buffed regen scaling)."""
    ds = calculate_derived(StatAllocation(15, 15, 20, 50))
    assert ds.energy_regen == 15


# --- DerivedStats: below-baseline behavior unchanged ---


def test_derived_low_power_damage_unchanged() -> None:
    """Power below 25 uses original linear scaling plus versatility bonus."""
    ds = calculate_derived(StatAllocation(15, 25, 35, 25))
    # variance = (100+0+100+0)/4 = 50, ratio=0.5, v_ratio=0.5
    # bonus_dmg = int(13 * 0.5) = 6
    assert ds.min_damage == max(1, int(15 * 0.6)) + 6  # 9 + 6 = 15
    assert ds.max_damage == int(15 * 1.4) + 6  # 21 + 6 = 27


def test_derived_at_baseline_power_damage_unchanged() -> None:
    """Power=25 (baseline, balanced) gives min=28, max=48 (with versatility bonus)."""
    ds = calculate_derived(DEFAULT_ALLOCATION)
    assert ds.min_damage == 28
    assert ds.max_damage == 48


def test_derived_extreme_power_damage_compressed() -> None:
    """Power=80 damage compressed vs old linear: min=31, max=79."""
    ds = calculate_derived(StatAllocation(80, 5, 10, 5))
    assert ds.min_damage == 31
    assert ds.max_damage == 79


def test_derived_dodge_below_baseline_unchanged() -> None:
    """Speed below 25 uses 0.3 scaling."""
    ds = calculate_derived(StatAllocation(25, 15, 35, 25))
    assert ds.dodge_chance == 4.5  # 15 * 0.3 = 4.5


# --- DerivedStats: versatility bonus ---


def test_versatility_bonus_default_full() -> None:
    """25/25/25/25 (zero variance) gets full versatility HP bonus."""
    ds = calculate_derived(DEFAULT_ALLOCATION)
    # 50 + 25*0.8 + 32 = 102
    assert ds.max_hp == 102


def test_versatility_bonus_specialist_zero() -> None:
    """High-variance build (specialist) gets no versatility HP bonus."""
    ds = calculate_derived(StatAllocation(50, 15, 15, 20))
    # variance = (625+100+100+25)/4 = 212.5 >= cap(100) → bonus=0
    # HP = 50 + 15*0.8 + 0 = 62
    assert ds.max_hp == 62


def test_versatility_bonus_partial() -> None:
    """Moderate-variance build gets no versatility bonus (at cap exactly)."""
    # Bruiser (35/15/35/15): variance = (100+100+100+100)/4 = 100
    # ratio = 100/100 = 1.0 → v_ratio = 0.0 → bonus = 0
    ds = calculate_derived(StatAllocation(35, 15, 35, 15))
    # HP = 50 + 35*0.8 + 0 = 78
    assert ds.max_hp == 78


def test_derived_is_frozen() -> None:
    """Cannot set attributes on DerivedStats instance."""
    ds = calculate_derived(DEFAULT_ALLOCATION)
    assert isinstance(ds, DerivedStats)
    with pytest.raises(AttributeError):
        ds.max_hp = 999  # type: ignore[misc]
