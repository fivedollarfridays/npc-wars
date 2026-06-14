"""Monte Carlo agreement tests for equipment-aware calculate_hit_probability.

Verifies the analytic expected_damage from calculate_hit_probability matches
the simulated mean damage-per-attack from roll_attack when both are given the
same equipment kwargs.
"""

from __future__ import annotations

import random

from engine.combat_rolls import calculate_hit_probability, roll_attack
from engine.stats import DEFAULT_ALLOCATION, calculate_derived

_DEFAULT = calculate_derived(DEFAULT_ALLOCATION)

# Non-trivial equipment: attacker wields a heavy weapon (+to_hit, +dmg, +crit),
# defender wears armor granting +dr.
_ATK_EQUIP = {
    "equipment_to_hit": 2,
    "equipment_min_dmg": 4,
    "equipment_max_dmg": 6,
    "equipment_crit_mult": 0.3,
}
_DEF_EQUIP = {
    "equipment_dr": 4,
}


def _simulate_mean_damage(n: int, seed: int) -> float:
    """Run roll_attack N times with equipment kwargs, return mean damage."""
    rng = random.Random(seed)
    total = 0.0
    for _ in range(n):
        result = roll_attack(
            _DEFAULT, _DEFAULT, rng=rng,
            equipment_to_hit=_ATK_EQUIP["equipment_to_hit"],
            equipment_min_dmg=_ATK_EQUIP["equipment_min_dmg"],
            equipment_max_dmg=_ATK_EQUIP["equipment_max_dmg"],
            equipment_crit_mult=_ATK_EQUIP["equipment_crit_mult"],
            equipment_dr=_DEF_EQUIP["equipment_dr"],
        )
        # Strip fractional tiebreaker component used for HP ordering.
        total += int(result.damage)
    return total / n


def test_monte_carlo_expected_damage_agreement() -> None:
    """Analytic expected_damage within 5% of simulated roll_attack mean."""
    analytic = calculate_hit_probability(
        _DEFAULT, _DEFAULT,
        equipment_to_hit=_ATK_EQUIP["equipment_to_hit"],
        equipment_min_dmg=_ATK_EQUIP["equipment_min_dmg"],
        equipment_max_dmg=_ATK_EQUIP["equipment_max_dmg"],
        equipment_crit_mult=_ATK_EQUIP["equipment_crit_mult"],
        equipment_dr=_DEF_EQUIP["equipment_dr"],
    )["expected_damage"]

    simulated = _simulate_mean_damage(n=20000, seed=1234)

    rel_error = abs(analytic - simulated) / simulated
    assert rel_error < 0.05, (
        f"analytic={analytic} simulated={simulated:.3f} "
        f"rel_error={rel_error:.4f} exceeds 5%"
    )


def test_bare_call_unchanged_no_equipment() -> None:
    """A bare call (no equipment) reproduces the no-equipment baseline."""
    bare = calculate_hit_probability(_DEFAULT, _DEFAULT)
    # Explicit zero-equipment kwargs must be identical to the bare call.
    explicit_zero = calculate_hit_probability(
        _DEFAULT, _DEFAULT,
        equipment_to_hit=0, equipment_min_dmg=0, equipment_max_dmg=0,
        equipment_crit_mult=0.0, equipment_dr=0, armor_pierce=0,
    )
    assert bare == explicit_zero


def test_equipment_dr_lowers_expected_damage() -> None:
    """Defender DR from armor lowers attacker's expected damage."""
    no_armor = calculate_hit_probability(
        _DEFAULT, _DEFAULT, equipment_min_dmg=4, equipment_max_dmg=6,
    )["expected_damage"]
    with_armor = calculate_hit_probability(
        _DEFAULT, _DEFAULT, equipment_min_dmg=4, equipment_max_dmg=6,
        equipment_dr=6,
    )["expected_damage"]
    assert with_armor < no_armor


def test_equipment_damage_raises_expected_damage() -> None:
    """Weapon min/max damage bonus raises attacker's expected damage."""
    base = calculate_hit_probability(_DEFAULT, _DEFAULT)["expected_damage"]
    boosted = calculate_hit_probability(
        _DEFAULT, _DEFAULT, equipment_min_dmg=4, equipment_max_dmg=6,
    )["expected_damage"]
    assert boosted > base
