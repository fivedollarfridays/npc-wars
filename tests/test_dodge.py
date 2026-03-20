"""Tests for dodge system — SPEED-based, halves damage on hit."""

from __future__ import annotations

import random

from engine.combat_rolls import CombatResult, roll_attack
from engine.stats import DEFAULT_ALLOCATION, DerivedStats, calculate_derived

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DEFAULT = calculate_derived(DEFAULT_ALLOCATION)


class MockRNG:
    """Controllable RNG for deterministic dodge testing.

    randint calls cycle: first call → d20, second call → damage.
    random() → returns dodge_value (< dodge_chance/100 means dodge).
    """

    def __init__(self, d20: int = 15, damage: int = 25, dodge: bool = True):
        self._d20 = d20
        self._damage = damage
        self._dodge_value = 0.0 if dodge else 1.0
        self._call_count = 0

    def randint(self, a: int, b: int) -> int:
        self._call_count += 1
        if a == 1 and b == 20:
            return self._d20
        return self._damage

    def random(self) -> float:
        return self._dodge_value


def _high_speed_stats() -> DerivedStats:
    """SPEED=50 → dodge_chance=20.0."""
    from engine.stats import validate_allocation, calculate_derived as calc

    alloc = validate_allocation(15, 50, 15, 20)
    return calc(alloc)


# ---------------------------------------------------------------------------
# Cycle 1: CombatResult has dodged field
# ---------------------------------------------------------------------------


def test_combat_result_has_dodged_field() -> None:
    """CombatResult dataclass includes a 'dodged' boolean field."""
    r = CombatResult(
        hit=True, damage=10, roll=15, modifier=2,
        target_ac=5, is_crit=False, is_miss=False, dodged=True,
    )
    assert r.dodged is True


def test_miss_has_dodged_false() -> None:
    """Missed attacks always have dodged=False."""
    rng = MockRNG(d20=1, dodge=True)  # d20=1 will miss high-AC defender
    defender = DerivedStats(
        max_hp=100, max_energy=100, min_damage=15, max_damage=35,
        crit_multiplier=1.5, dodge_chance=10.0, initiative=25,
        damage_reduction=30, energy_regen=0,
    )
    result = roll_attack(_DEFAULT, defender, rng=rng)
    assert result.hit is False
    assert result.dodged is False


# ---------------------------------------------------------------------------
# Cycle 2: Dodge halves damage / no dodge full damage
# ---------------------------------------------------------------------------


def test_dodge_halves_damage() -> None:
    """When dodge triggers, damage is halved (integer division)."""
    # d20=10, modifier=2, total=12, AC=8 → hit, NOT crit (12 < 8+15=23)
    rng = MockRNG(d20=10, damage=30, dodge=True)
    result = roll_attack(_DEFAULT, _DEFAULT, rng=rng)
    assert result.hit is True
    assert result.is_crit is False
    assert result.dodged is True
    # 30.10 / 2 = 15.05 (fractional tiebreaker)
    assert int(result.damage) == 15


def test_no_dodge_full_damage() -> None:
    """When dodge does not trigger, full damage is dealt."""
    rng = MockRNG(d20=10, damage=30, dodge=False)
    result = roll_attack(_DEFAULT, _DEFAULT, rng=rng)
    assert result.hit is True
    assert result.is_crit is False
    assert result.dodged is False
    assert int(result.damage) == 30


def test_dodged_crit_still_halved() -> None:
    """Crit + dodge → crit damage is halved."""
    # d20=20 → natural crit, damage=30, crit_mult=1.5 → 45 → dodge halves → 22
    rng = MockRNG(d20=20, damage=30, dodge=True)
    result = roll_attack(_DEFAULT, _DEFAULT, rng=rng)
    assert result.hit is True
    assert result.is_crit is True
    assert result.dodged is True
    crit_damage = int(30 * _DEFAULT.crit_multiplier)
    expected = max(1, crit_damage // 2)
    assert int(result.damage) == expected


def test_dodge_minimum_1_damage() -> None:
    """Dodged hit deals at least 1 damage even with low base."""
    low = DerivedStats(
        max_hp=100, max_energy=100, min_damage=1, max_damage=2,
        crit_multiplier=1.5, dodge_chance=10.0, initiative=25,
        damage_reduction=0, energy_regen=0,
    )
    rng = MockRNG(d20=15, damage=1, dodge=True)
    result = roll_attack(low, _DEFAULT, rng=rng)
    assert result.hit is True
    assert result.dodged is True
    assert result.damage >= 1


# ---------------------------------------------------------------------------
# Cycle 3: Statistical dodge rates
# ---------------------------------------------------------------------------


def test_dodge_chance_default_10pct() -> None:
    """1000 attacks at default stats (~10% dodge_chance) → ~10% dodged."""
    rng = random.Random(42)
    results = [roll_attack(_DEFAULT, _DEFAULT, rng=rng) for _ in range(1000)]
    hits = [r for r in results if r.hit]
    dodged = [r for r in hits if r.dodged]
    rate = len(dodged) / len(hits)
    assert 0.05 <= rate <= 0.18, f"Dodge rate {rate:.3f} outside expected range"


def test_high_speed_more_dodges() -> None:
    """SPEED=50 → dodge_chance=20% → more dodges than default."""
    fast = _high_speed_stats()
    rng1 = random.Random(42)
    rng2 = random.Random(42)
    default_dodges = sum(
        1 for _ in range(1000)
        if (r := roll_attack(_DEFAULT, _DEFAULT, rng=rng1)).hit and r.dodged
    )
    fast_dodges = sum(
        1 for _ in range(1000)
        if (r := roll_attack(_DEFAULT, fast, rng=rng2)).hit and r.dodged
    )
    assert fast_dodges > default_dodges


# ---------------------------------------------------------------------------
# Cycle 4: Hit event includes dodged field (rounds_combat.py)
# ---------------------------------------------------------------------------


def _make_bot(emoji: str, x: int = 0, y: int = 0):  # -> Bot
    from engine.combat import Bot
    return Bot(
        name=f"bot-{emoji}", emoji=emoji, bio="test", author="test",
        decide_func=lambda s: ("rest",), x=x, y=y,
    )


def test_hit_event_has_dodged_field() -> None:
    """Hit events from _roll_melee include 'dodged' key."""
    from engine.rounds_combat import resolve_attacks

    b1 = _make_bot("A", x=0, y=0)
    b2 = _make_bot("B", x=1, y=0)
    actions = {"A": ("attack", "east"), "B": ("defend",)}
    rng = random.Random(0)
    events = resolve_attacks([b1, b2], actions, rng=rng)
    hit_events = [e for e in events if e["type"] == "hit"]
    for evt in hit_events:
        assert "dodged" in evt, f"Hit event missing 'dodged' key: {evt}"


# ---------------------------------------------------------------------------
# Cycle 5: Feed shows "(glancing)" for dodged hits
# ---------------------------------------------------------------------------


def test_feed_shows_glancing() -> None:
    """Feed formatter shows '(glancing)' for dodged hits."""
    from agentgrounds.wars.cli.feed import format_feed_event

    evt = {"type": "hit", "attacker": "A", "target": "B",
           "damage": 15, "is_crit": False, "dodged": True}
    line = format_feed_event(evt, 3)
    assert line is not None
    assert "(glancing)" in line


def test_feed_no_glancing_for_normal_hit() -> None:
    """Feed does NOT show '(glancing)' for normal (non-dodged) hits."""
    from agentgrounds.wars.cli.feed import format_feed_event

    evt = {"type": "hit", "attacker": "A", "target": "B",
           "damage": 30, "is_crit": False, "dodged": False}
    line = format_feed_event(evt, 3)
    assert line is not None
    assert "(glancing)" not in line
