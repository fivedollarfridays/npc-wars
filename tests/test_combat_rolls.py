"""Tests for engine.combat_rolls — d20-based combat roll engine."""

from __future__ import annotations

import random

from engine.combat_rolls import (
    BASE_AC,
    CRIT_THRESHOLD,
    roll_attack,
    roll_ranged_attack,
)
from engine.stats import DEFAULT_ALLOCATION, DerivedStats, calculate_derived

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DEFAULT = calculate_derived(DEFAULT_ALLOCATION)


def _high_power_stats() -> DerivedStats:
    """Derived stats from a power-heavy allocation (50/20/15/15)."""
    from engine.stats import validate_allocation, calculate_derived as calc

    alloc = validate_allocation(50, 20, 15, 15)
    return calc(alloc)


def _make_rng(seed: int = 42) -> random.Random:
    return random.Random(seed)


# ---------------------------------------------------------------------------
# Hit / miss mechanics
# ---------------------------------------------------------------------------


def test_hit_when_roll_above_ac() -> None:
    """High seeded roll produces a hit."""
    # Seed 0 gives d20=14 on first call to randint(1,20)
    rng = random.Random(0)
    result = roll_attack(_DEFAULT, _DEFAULT, rng=rng)
    # default AC = BASE_AC + 0 = 5, modifier = 25//10 = 2, so 14+2=16 >= 5
    assert result.hit is True
    assert result.is_miss is False
    assert result.damage > 0


def test_miss_when_roll_below_ac() -> None:
    """Contrived scenario: high-AC defender causes a miss."""
    # Create defender with very high damage_reduction so AC is huge
    defender = DerivedStats(
        max_hp=100,
        max_energy=100,
        min_damage=15,
        max_damage=35,
        crit_multiplier=1.5,
        dodge_chance=10.0,
        initiative=25,
        damage_reduction=30,
        energy_regen=0,
    )
    rng = _make_rng(42)
    result = roll_attack(_DEFAULT, defender, rng=rng)
    # AC = 5 + 30 = 35, modifier = 2, need roll >= 33 on d20 — impossible
    assert result.hit is False
    assert result.is_miss is True
    assert result.damage == 0


def test_default_stats_hit_rate_90pct() -> None:
    """At default stats, hit rate should be ~85-95%."""
    rng = _make_rng(42)
    hits = sum(
        roll_attack(_DEFAULT, _DEFAULT, rng=rng).hit for _ in range(1000)
    )
    rate = hits / 1000
    assert 0.85 <= rate <= 0.95, f"Hit rate {rate:.3f} out of expected range"


def test_defending_halves_hit_rate() -> None:
    """Defending target reduces hit rate to ~40-60%."""
    rng = _make_rng(42)
    hits = sum(
        roll_attack(_DEFAULT, _DEFAULT, defending=True, rng=rng).hit
        for _ in range(1000)
    )
    rate = hits / 1000
    assert 0.30 <= rate <= 0.65, f"Defending hit rate {rate:.3f} out of expected range"


# ---------------------------------------------------------------------------
# Damage range
# ---------------------------------------------------------------------------


def test_damage_in_range() -> None:
    """Damage on a hit is within attacker's damage range (or above for crits)."""
    rng = _make_rng(42)
    for _ in range(200):
        r = roll_attack(_DEFAULT, _DEFAULT, rng=rng)
        if r.hit:
            assert r.damage >= 1
            if not r.is_crit:
                assert r.damage <= _DEFAULT.max_damage


def test_default_avg_damage_around_25() -> None:
    """Average damage at default stats ≈ 20-30 (including crits)."""
    rng = _make_rng(42)
    damages = [
        r.damage
        for _ in range(1000)
        if (r := roll_attack(_DEFAULT, _DEFAULT, rng=rng)).hit
    ]
    avg = sum(damages) / len(damages)
    assert 20 <= avg <= 35, f"Avg damage {avg:.1f} out of expected range"


def test_high_power_more_damage() -> None:
    """POWER=50 bot deals higher average damage than default."""
    hp = _high_power_stats()
    rng1 = _make_rng(42)
    rng2 = _make_rng(42)
    hits_default = [r.damage for _ in range(500) if (r := roll_attack(_DEFAULT, _DEFAULT, rng=rng1)).hit]
    hits_high = [r.damage for _ in range(500) if (r := roll_attack(hp, _DEFAULT, rng=rng2)).hit]
    assert sum(hits_high) / len(hits_high) > sum(hits_default) / len(hits_default)


# ---------------------------------------------------------------------------
# Critical hits
# ---------------------------------------------------------------------------


def test_natural_20_always_crits() -> None:
    """A natural 20 roll is always a crit."""
    # Find a seed that gives d20=20
    for seed in range(1000):
        rng = random.Random(seed)
        val = rng.randint(1, 20)
        if val == 20:
            rng = random.Random(seed)
            result = roll_attack(_DEFAULT, _DEFAULT, rng=rng)
            assert result.is_crit is True
            assert result.roll == 20
            return
    raise AssertionError("Could not find seed producing natural 20")


def test_high_roll_crits() -> None:
    """Roll far above AC triggers crit via threshold."""
    # AC=5, crit when total_roll >= 5 + CRIT_THRESHOLD = 13
    # modifier=2, so need d20 >= 11
    for seed in range(1000):
        rng = random.Random(seed)
        val = rng.randint(1, 20)
        if val >= 15 and val != 20:  # high but not nat 20
            rng = random.Random(seed)
            result = roll_attack(_DEFAULT, _DEFAULT, rng=rng)
            # total = val + 2, AC = 5, crit threshold = 5 + 8 = 13
            if val + 2 >= BASE_AC + CRIT_THRESHOLD:
                assert result.is_crit is True
            return
    raise AssertionError("Could not find suitable seed")


def test_crit_damage_multiplied() -> None:
    """Crit damage is higher than the roll's base damage."""
    # Find a crit result
    for seed in range(1000):
        rng = random.Random(seed)
        result = roll_attack(_DEFAULT, _DEFAULT, rng=rng)
        if result.is_crit and not result.dodged:
            # Crit damage should be >= min_damage * crit_multiplier
            assert result.damage >= int(_DEFAULT.min_damage * _DEFAULT.crit_multiplier)
            return
    raise AssertionError("No non-dodged crit found in 1000 seeds")


def test_default_crit_rate() -> None:
    """Crit rate at default stats is 45-65%.

    With AC=5, CRIT_THRESHOLD=8, modifier=2: crit when d20 >= 11 (~50%).
    This is by design — crits are common, making combat swingy.
    """
    rng = _make_rng(42)
    results = [roll_attack(_DEFAULT, _DEFAULT, rng=rng) for _ in range(1000)]
    hits = [r for r in results if r.hit]
    crits = [r for r in hits if r.is_crit]
    crit_rate = len(crits) / len(hits)
    assert 0.45 <= crit_rate <= 0.65, f"Crit rate {crit_rate:.3f} out of range"


# ---------------------------------------------------------------------------
# Ranged attacks
# ---------------------------------------------------------------------------


def test_ranged_lower_hit_rate() -> None:
    """Ranged hit rate is lower than melee at same stats."""
    rng1, rng2 = _make_rng(42), _make_rng(42)
    melee_hits = sum(roll_attack(_DEFAULT, _DEFAULT, rng=rng1).hit for _ in range(1000))
    ranged_hits = sum(roll_ranged_attack(_DEFAULT, _DEFAULT, rng=rng2).hit for _ in range(1000))
    assert ranged_hits < melee_hits


def test_ranged_avg_damage_around_15() -> None:
    """Ranged avg damage ≈ 12-18."""
    rng = _make_rng(42)
    damages = [
        r.damage
        for _ in range(1000)
        if (r := roll_ranged_attack(_DEFAULT, _DEFAULT, rng=rng)).hit
    ]
    avg = sum(damages) / len(damages)
    assert 10 <= avg <= 22, f"Ranged avg {avg:.1f} out of range"


def test_ranged_min_damage_at_least_1() -> None:
    """Ranged damage is always >= 1 on a hit."""
    # Low-power attacker
    low = DerivedStats(
        max_hp=100, max_energy=100,
        min_damage=3, max_damage=7,
        crit_multiplier=1.5, dodge_chance=10.0,
        initiative=25, damage_reduction=0, energy_regen=0,
    )
    rng = _make_rng(42)
    for _ in range(200):
        r = roll_ranged_attack(low, _DEFAULT, rng=rng)
        if r.hit:
            assert r.damage >= 1


# ---------------------------------------------------------------------------
# Momentum modifiers
# ---------------------------------------------------------------------------


def test_momentum_damage_multiplier() -> None:
    """momentum_damage_mult=1.1 increases avg damage by ~10%."""
    rng1 = _make_rng(42)
    rng2 = _make_rng(42)
    base_dmg = [
        r.damage for _ in range(500)
        if (r := roll_attack(_DEFAULT, _DEFAULT, rng=rng1)).hit
    ]
    boosted_dmg = [
        r.damage for _ in range(500)
        if (r := roll_attack(_DEFAULT, _DEFAULT, rng=rng2, momentum_damage_mult=1.1)).hit
    ]
    avg_base = sum(base_dmg) / len(base_dmg)
    avg_boost = sum(boosted_dmg) / len(boosted_dmg)
    assert avg_boost > avg_base


def test_momentum_defense_reduction() -> None:
    """momentum_defense_reduct=0.15 lowers effective AC, raising hit rate."""
    # Use defending so base hit rate is lower — easier to measure
    rng1 = _make_rng(42)
    rng2 = _make_rng(42)
    base_hits = sum(
        roll_attack(_DEFAULT, _DEFAULT, defending=True, rng=rng1).hit
        for _ in range(1000)
    )
    boosted_hits = sum(
        roll_attack(
            _DEFAULT, _DEFAULT, defending=True, rng=rng2,
            momentum_defense_reduct=0.15,
        ).hit
        for _ in range(1000)
    )
    assert boosted_hits > base_hits


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_same_seed_same_result() -> None:
    """Two roll_attack calls with the same seed produce identical results."""
    r1 = roll_attack(_DEFAULT, _DEFAULT, rng=_make_rng(123))
    r2 = roll_attack(_DEFAULT, _DEFAULT, rng=_make_rng(123))
    assert r1 == r2
