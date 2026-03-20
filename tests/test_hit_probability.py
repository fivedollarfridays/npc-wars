"""Tests for hit probability calculator and state dict wiring."""

from __future__ import annotations

from engine.combat_rolls import calculate_hit_probability
from engine.stats import (
    DEFAULT_ALLOCATION,
    DerivedStats,
    calculate_derived,
    validate_allocation,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DEFAULT = calculate_derived(DEFAULT_ALLOCATION)


def _high_armor_stats() -> DerivedStats:
    """Derived stats from armor-heavy allocation (15/5/75/5)."""
    alloc = validate_allocation(15, 5, 75, 5)
    return calculate_derived(alloc)


def _high_speed_stats() -> DerivedStats:
    """Derived stats from speed-heavy allocation (15/60/10/15)."""
    alloc = validate_allocation(15, 60, 10, 15)
    return calculate_derived(alloc)


# ---------------------------------------------------------------------------
# Pure calculator tests
# ---------------------------------------------------------------------------


def test_default_vs_default_hit_chance() -> None:
    """Both at default stats. hit_chance should be ~65-85% (AC=8, mod=+2)."""
    result = calculate_hit_probability(_DEFAULT, _DEFAULT)
    assert 65.0 <= result["hit_chance"] <= 85.0, (
        f"Expected ~75%, got {result['hit_chance']}%"
    )


def test_defending_reduces_hit_chance() -> None:
    """Defending target (AC=14): hit_chance should drop to ~35-55%."""
    result = calculate_hit_probability(_DEFAULT, _DEFAULT, defending=True)
    assert 35.0 <= result["hit_chance"] <= 55.0, (
        f"Expected ~45%, got {result['hit_chance']}%"
    )


def test_high_armor_reduces_hit_chance() -> None:
    """High-armor defender has lower hit chance than default."""
    default_result = calculate_hit_probability(_DEFAULT, _DEFAULT)
    armor_result = calculate_hit_probability(_DEFAULT, _high_armor_stats())
    assert armor_result["hit_chance"] < default_result["hit_chance"]


def test_high_speed_attacker_higher_modifier() -> None:
    """High-speed attacker has higher initiative -> better hit chance."""
    default_result = calculate_hit_probability(_DEFAULT, _DEFAULT)
    speed_result = calculate_hit_probability(_high_speed_stats(), _DEFAULT)
    assert speed_result["hit_chance"] >= default_result["hit_chance"]


def test_crit_chance_positive() -> None:
    """Crit chance is positive for default stats."""
    result = calculate_hit_probability(_DEFAULT, _DEFAULT)
    assert result["crit_chance"] > 0.0


def test_dodge_chance_matches_defender() -> None:
    """dodge_chance in result matches defender's derived dodge_chance."""
    result = calculate_hit_probability(_DEFAULT, _DEFAULT)
    assert result["dodge_chance"] == _DEFAULT.dodge_chance

    fast = _high_speed_stats()
    result2 = calculate_hit_probability(_DEFAULT, fast)
    assert result2["dodge_chance"] == fast.dodge_chance


def test_expected_damage_positive() -> None:
    """Expected damage is positive for default stats."""
    result = calculate_hit_probability(_DEFAULT, _DEFAULT)
    assert result["expected_damage"] > 0.0


def test_to_hit_modifier_raises_chance() -> None:
    """Positive to_hit_modifier increases hit chance."""
    base = calculate_hit_probability(_DEFAULT, _DEFAULT)
    boosted = calculate_hit_probability(
        _DEFAULT, _DEFAULT, to_hit_modifier=3,
    )
    assert boosted["hit_chance"] >= base["hit_chance"]


def test_result_keys() -> None:
    """Result dict has exactly the expected keys."""
    result = calculate_hit_probability(_DEFAULT, _DEFAULT)
    expected_keys = {"hit_chance", "crit_chance", "dodge_chance", "expected_damage"}
    assert set(result.keys()) == expected_keys


def test_nat20_floor_on_hit_chance() -> None:
    """Even vs impossible AC, hit_chance is at least 5% (nat 20)."""
    tank = DerivedStats(
        max_hp=200, max_energy=100,
        min_damage=5, max_damage=10,
        crit_multiplier=1.5, dodge_chance=0.0,
        initiative=25, damage_reduction=30,
        energy_regen=0,
    )
    result = calculate_hit_probability(_DEFAULT, tank)
    assert result["hit_chance"] >= 5.0


def test_nat20_floor_on_crit_chance() -> None:
    """Crit chance is at least 5% (nat 20 always crits)."""
    result = calculate_hit_probability(_DEFAULT, _DEFAULT)
    assert result["crit_chance"] >= 5.0
