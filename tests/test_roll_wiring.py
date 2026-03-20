"""Tests for wiring roll_attack / roll_ranged_attack into resolve_attacks / resolve_ranged_attacks."""

import random

from tests.conftest import make_bot
from engine.rounds import resolve_attacks, resolve_ranged_attacks


# ---------------------------------------------------------------------------
# Cycle 1: Hit events carry roll metadata
# ---------------------------------------------------------------------------


def test_resolve_attacks_hit_event_has_roll_data():
    """When rng is provided and attack hits, event includes roll/modifier/ac/is_crit."""
    attacker = make_bot(emoji="A", x=5, y=5)
    defender = make_bot(emoji="D", x=5, y=4)  # north of attacker
    actions = {"A": ("attack", "north"), "D": ("rest",)}
    # Seed 42: we need a seed that produces a hit
    rng = random.Random(42)
    events = resolve_attacks([attacker, defender], actions, rng=rng)

    hits = [e for e in events if e["type"] == "hit"]
    assert len(hits) == 1, f"Expected 1 hit, got {events}"
    hit = hits[0]
    assert "roll" in hit, "Hit event should contain 'roll' field"
    assert "modifier" in hit, "Hit event should contain 'modifier' field"
    assert "ac" in hit, "Hit event should contain 'ac' field"
    assert "is_crit" in hit, "Hit event should contain 'is_crit' field"
    assert isinstance(hit["roll"], int)
    assert isinstance(hit["damage"], (int, float))
    assert hit["damage"] > 0


def test_resolve_attacks_damage_applied_with_rng():
    """After a hit with rng, target.hp is reduced and bot.damage_dealt increased."""
    attacker = make_bot(emoji="A", x=5, y=5)
    defender = make_bot(emoji="D", x=5, y=4, hp=100)
    actions = {"A": ("attack", "north"), "D": ("rest",)}
    # Use seed that produces a hit (high roll)
    rng = random.Random(42)
    hp_before = defender.hp
    dd_before = attacker.damage_dealt

    events = resolve_attacks([attacker, defender], actions, rng=rng)

    hits = [e for e in events if e["type"] == "hit"]
    if hits:
        assert defender.hp < hp_before, "Target HP should decrease after hit"
        assert attacker.damage_dealt > dd_before, "Attacker damage_dealt should increase"
        assert defender.damage_taken > 0, "Defender damage_taken should increase"


# ---------------------------------------------------------------------------
# Cycle 2: Miss events
# ---------------------------------------------------------------------------


def test_resolve_attacks_miss_produces_attack_miss():
    """When roll < AC with rng, event type is 'attack_miss' with roll data."""
    # Use defending target for higher AC (easier to miss)
    actions = {"A": ("attack", "north"), "D": ("defend",)}

    for seed in range(500):
        a = make_bot(emoji="A", x=5, y=5)
        d = make_bot(emoji="D", x=5, y=4, hp=100)
        rng = random.Random(seed)
        events = resolve_attacks([a, d], actions, rng=rng)
        misses = [e for e in events if e["type"] == "attack_miss"]
        if misses:
            miss = misses[0]
            assert miss["attacker"] == "A"
            assert miss["target"] == "D"
            assert "roll" in miss
            assert "modifier" in miss
            assert "ac" in miss
            return

    raise AssertionError("Could not find a seed that produces a miss")


def test_resolve_attacks_no_target_still_miss():
    """When no target at position, event type is 'miss' (unchanged from before)."""
    attacker = make_bot(emoji="A", x=5, y=5)
    actions = {"A": ("attack", "north")}
    rng = random.Random(42)

    events = resolve_attacks([attacker], actions, rng=rng)

    assert len(events) == 1
    assert events[0]["type"] == "miss"
    assert events[0]["attacker"] == "A"
    assert events[0]["direction"] == "north"


# ---------------------------------------------------------------------------
# Cycle 3: Defending target and backward compat
# ---------------------------------------------------------------------------


def test_resolve_attacks_defending_target_higher_ac():
    """Defending target should have higher AC in events than resting target."""
    # Run same seed twice: once with defender resting, once defending
    seed = 42
    actions_rest = {"A": ("attack", "north"), "D": ("rest",)}
    actions_defend = {"A": ("attack", "north"), "D": ("defend",)}

    a1 = make_bot(emoji="A", x=5, y=5)
    d1 = make_bot(emoji="D", x=5, y=4, hp=100)
    rng1 = random.Random(seed)
    events_rest = resolve_attacks([a1, d1], actions_rest, rng=rng1)

    a2 = make_bot(emoji="A", x=5, y=5)
    d2 = make_bot(emoji="D", x=5, y=4, hp=100)
    rng2 = random.Random(seed)
    events_defend = resolve_attacks([a2, d2], actions_defend, rng=rng2)

    # Extract AC from whichever event type we got
    def get_ac(evts):
        for e in evts:
            if "ac" in e:
                return e["ac"]
        return None

    ac_rest = get_ac(events_rest)
    ac_defend = get_ac(events_defend)
    assert ac_rest is not None, f"No AC in events: {events_rest}"
    assert ac_defend is not None, f"No AC in events: {events_defend}"
    assert ac_defend > ac_rest, (
        f"Defending AC ({ac_defend}) should be higher than resting AC ({ac_rest})"
    )


def test_resolve_attacks_without_rng_backward_compat():
    """When rng is None, resolve_attacks still works (flat damage fallback)."""
    attacker = make_bot(emoji="A", x=5, y=5)
    defender = make_bot(emoji="D", x=5, y=4, hp=100)
    actions = {"A": ("attack", "north"), "D": ("rest",)}

    events = resolve_attacks([attacker, defender], actions)

    # Should produce a hit with damage (flat path)
    hits = [e for e in events if e["type"] == "hit"]
    assert len(hits) == 1, f"Expected 1 hit, got {events}"
    assert hits[0]["damage"] > 0


# ---------------------------------------------------------------------------
# Cycle 4: Ranged attacks with roll system (T28.5)
# ---------------------------------------------------------------------------


def test_ranged_with_rng_uses_rolls():
    """When rng is provided and ranged attack hits, event includes roll/ac fields."""
    actions = {"R": ("ranged_attack", "north"), "T": ("rest",)}

    # Try seeds until we get a hit
    for seed in range(200):
        a = make_bot(emoji="R", x=5, y=5)
        d = make_bot(emoji="T", x=5, y=3, hp=100)
        rng = random.Random(seed)
        events = resolve_ranged_attacks([a, d], actions, rng=rng)
        hits = [e for e in events if e["type"] == "ranged_hit"]
        if hits:
            hit = hits[0]
            assert "roll" in hit, "ranged_hit should contain 'roll' field"
            assert "ac" in hit, "ranged_hit should contain 'ac' field"
            assert "modifier" in hit, "ranged_hit should contain 'modifier' field"
            assert "is_crit" in hit, "ranged_hit should contain 'is_crit' field"
            assert isinstance(hit["roll"], int)
            assert isinstance(hit["damage"], (int, float))
            assert hit["damage"] > 0
            return

    raise AssertionError("Could not find a seed that produces a ranged hit")


def test_ranged_miss_produces_ranged_attack_miss():
    """When roll < AC with rng, event type is 'ranged_attack_miss' with roll data."""
    actions = {"R": ("ranged_attack", "north"), "T": ("rest",)}

    for seed in range(200):
        a = make_bot(emoji="R", x=5, y=5)
        d = make_bot(emoji="T", x=5, y=3, hp=100)
        rng = random.Random(seed)
        events = resolve_ranged_attacks([a, d], actions, rng=rng)
        misses = [e for e in events if e["type"] == "ranged_attack_miss"]
        if misses:
            miss = misses[0]
            assert miss["attacker"] == "R"
            assert miss["target"] == "T"
            assert "roll" in miss
            assert "modifier" in miss
            assert "ac" in miss
            return

    raise AssertionError("Could not find a seed that produces a ranged miss")


def test_ranged_no_target_unchanged():
    """When no target at ranged position, event type is 'ranged_miss' (unchanged)."""
    attacker = make_bot(emoji="R", x=5, y=5)
    actions = {"R": ("ranged_attack", "north")}
    rng = random.Random(42)

    events = resolve_ranged_attacks([attacker], actions, rng=rng)

    assert len(events) == 1
    assert events[0]["type"] == "ranged_miss"
    assert events[0]["attacker"] == "R"
    assert events[0]["direction"] == "north"


def test_ranged_damage_applied():
    """Target hp reduced and attacker damage_dealt increased after ranged hit."""
    actions = {"R": ("ranged_attack", "north"), "T": ("rest",)}

    for seed in range(200):
        a = make_bot(emoji="R", x=5, y=5)
        d = make_bot(emoji="T", x=5, y=3, hp=100)
        rng = random.Random(seed)
        hp_before = d.hp
        dd_before = a.damage_dealt
        events = resolve_ranged_attacks([a, d], actions, rng=rng)
        hits = [e for e in events if e["type"] == "ranged_hit"]
        if hits:
            assert d.hp < hp_before, "Target HP should decrease after ranged hit"
            assert a.damage_dealt > dd_before, "Attacker damage_dealt should increase"
            assert d.damage_taken > 0, "Defender damage_taken should increase"
            return

    raise AssertionError("Could not find a seed that produces a ranged hit")


def test_ranged_without_rng_flat_damage():
    """When rng is None, resolve_ranged_attacks uses flat 15 damage (backward compat)."""
    attacker = make_bot(emoji="R", x=5, y=5)
    defender = make_bot(emoji="T", x=5, y=3, hp=100)
    actions = {"R": ("ranged_attack", "north"), "T": ("rest",)}

    events = resolve_ranged_attacks([attacker, defender], actions)

    hits = [e for e in events if e["type"] == "ranged_hit"]
    assert len(hits) == 1, f"Expected 1 ranged_hit, got {events}"
    assert hits[0]["damage"] == 15
    assert defender.hp == 85
