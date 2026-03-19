"""Integration tests verifying combat event schemas carry roll/crit/miss data.

T28.6: Verify that all combat events include the expected fields after
T28.4 (melee roll wiring) and T28.5 (ranged roll wiring).
"""

import random

import pytest

from engine.game import run_match
from engine.rounds import resolve_attacks, resolve_ranged_attacks
from tests.conftest import make_bot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _collect_events(match_data: dict) -> list[dict]:
    """Flatten all events from all rounds."""
    events = []
    for rd in match_data.get("rounds", []):
        events.extend(rd.get("events", []))
    return events


def _chase_and_attack(state):
    """Bot that moves toward nearest enemy and attacks when adjacent."""
    me = state["me"]
    enemies = state["enemies"]
    if not enemies:
        return ("rest",)
    target = min(enemies, key=lambda e: abs(e["x"] - me["x"]) + abs(e["y"] - me["y"]))
    dx = target["x"] - me["x"]
    dy = target["y"] - me["y"]
    if abs(dx) + abs(dy) == 1:
        if dx == 1:
            return ("attack", "east")
        if dx == -1:
            return ("attack", "west")
        if dy == 1:
            return ("attack", "south")
        return ("attack", "north")
    if abs(dx) >= abs(dy):
        return ("move", "east") if dx > 0 else ("move", "west")
    return ("move", "south") if dy > 0 else ("move", "north")


def _ranged_attacker(state):
    """Bot that always tries ranged_attack north."""
    return ("ranged_attack", "north")


def _make_configs() -> list[dict]:
    """Four aggressive bots for match-level tests."""
    return [
        {"name": "A", "emoji": "A", "bio": "", "author": "t", "decide_func": _chase_and_attack},
        {"name": "B", "emoji": "B", "bio": "", "author": "t", "decide_func": _chase_and_attack},
        {"name": "C", "emoji": "C", "bio": "", "author": "t", "decide_func": _chase_and_attack},
        {"name": "D", "emoji": "D", "bio": "", "author": "t", "decide_func": _chase_and_attack},
    ]


# ---------------------------------------------------------------------------
# Cycle 1: Melee hit events have roll fields
# ---------------------------------------------------------------------------


def test_hit_event_has_roll_fields():
    """A 'hit' event from a seeded match must contain roll/modifier/ac/is_crit."""
    match_data = run_match(_make_configs(), seed=42)
    events = _collect_events(match_data)
    hits = [e for e in events if e["type"] == "hit"]
    assert len(hits) > 0, "Expected at least one hit event in the match"
    for hit in hits:
        assert "roll" in hit, f"Hit event missing 'roll': {hit}"
        assert "modifier" in hit, f"Hit event missing 'modifier': {hit}"
        assert "ac" in hit, f"Hit event missing 'ac': {hit}"
        assert "is_crit" in hit, f"Hit event missing 'is_crit': {hit}"


def test_attack_miss_event_has_roll_fields():
    """An 'attack_miss' event must contain roll/modifier/ac."""
    match_data = run_match(_make_configs(), seed=42)
    events = _collect_events(match_data)
    misses = [e for e in events if e["type"] == "attack_miss"]
    if not misses:
        pytest.skip("No attack_miss events in seed=42 match")
    for miss in misses:
        assert "roll" in miss, f"attack_miss missing 'roll': {miss}"
        assert "modifier" in miss, f"attack_miss missing 'modifier': {miss}"
        assert "ac" in miss, f"attack_miss missing 'ac': {miss}"


# ---------------------------------------------------------------------------
# Cycle 2: No-target miss events unchanged
# ---------------------------------------------------------------------------


def test_miss_event_unchanged():
    """A 'miss' (no target) event has direction but no roll fields."""
    # Unit test: attack with no target at target position
    attacker = make_bot(emoji="A", x=5, y=5)
    actions = {"A": ("attack", "north")}
    rng = random.Random(42)
    events = resolve_attacks([attacker], actions, rng=rng)
    assert len(events) == 1
    miss = events[0]
    assert miss["type"] == "miss"
    assert "direction" in miss, f"miss missing 'direction': {miss}"
    assert "attacker" in miss, f"miss missing 'attacker': {miss}"
    assert "roll" not in miss, f"miss should NOT have 'roll': {miss}"


# ---------------------------------------------------------------------------
# Cycle 3: Bool and damage checks
# ---------------------------------------------------------------------------


def test_events_crit_field_is_bool():
    """is_crit must be bool, not int or None."""
    match_data = run_match(_make_configs(), seed=42)
    events = _collect_events(match_data)
    hits = [e for e in events if e["type"] == "hit"]
    assert len(hits) > 0, "Expected hit events"
    for hit in hits:
        assert isinstance(hit["is_crit"], bool), (
            f"is_crit should be bool, got {type(hit['is_crit'])}: {hit}"
        )


def test_all_hit_events_have_positive_damage():
    """Every hit and ranged_hit must have damage > 0."""
    match_data = run_match(_make_configs(), seed=42)
    events = _collect_events(match_data)
    hit_types = {"hit", "ranged_hit"}
    hits = [e for e in events if e["type"] in hit_types]
    assert len(hits) > 0, "Expected at least one hit event"
    for hit in hits:
        assert "damage" in hit, f"Hit missing 'damage': {hit}"
        assert hit["damage"] > 0, f"Hit damage should be positive: {hit}"


# ---------------------------------------------------------------------------
# Cycle 4: Match-level roll data presence
# ---------------------------------------------------------------------------


def test_match_data_contains_roll_events():
    """A full match should have at least some events with roll data."""
    match_data = run_match(_make_configs(), seed=42)
    events = _collect_events(match_data)
    with_roll = [e for e in events if "roll" in e]
    assert len(with_roll) > 0, "Expected some events to carry roll data"


# ---------------------------------------------------------------------------
# Cycle 5: Unit-level ranged event schema
# ---------------------------------------------------------------------------


def test_ranged_hit_has_roll_fields():
    """ranged_hit events should carry roll/modifier/ac/is_crit."""
    # Try multiple seeds to find one that produces a ranged hit
    for seed in range(50):
        attacker = make_bot(emoji="A", x=5, y=5)
        target = make_bot(emoji="T", x=5, y=3)  # 2 squares north
        actions = {"A": ("ranged_attack", "north"), "T": ("rest",)}
        rng = random.Random(seed)
        events = resolve_ranged_attacks([attacker, target], actions, rng=rng)
        hits = [e for e in events if e["type"] == "ranged_hit"]
        if hits:
            for hit in hits:
                assert "roll" in hit, f"ranged_hit missing 'roll': {hit}"
                assert "modifier" in hit, f"ranged_hit missing 'modifier': {hit}"
                assert "ac" in hit, f"ranged_hit missing 'ac': {hit}"
                assert "is_crit" in hit, f"ranged_hit missing 'is_crit': {hit}"
                assert isinstance(hit["is_crit"], bool)
            return
    pytest.skip("No seed produced a ranged_hit in 50 attempts")


def test_ranged_attack_miss_has_roll_fields():
    """ranged_attack_miss events should carry roll/modifier/ac."""
    for seed in range(50):
        attacker = make_bot(emoji="A", x=5, y=5)
        target = make_bot(emoji="T", x=5, y=3)
        actions = {"A": ("ranged_attack", "north"), "T": ("rest",)}
        rng = random.Random(seed)
        events = resolve_ranged_attacks([attacker, target], actions, rng=rng)
        misses = [e for e in events if e["type"] == "ranged_attack_miss"]
        if misses:
            for miss in misses:
                assert "roll" in miss, f"ranged_attack_miss missing 'roll': {miss}"
                assert "modifier" in miss, f"ranged_attack_miss missing 'modifier': {miss}"
                assert "ac" in miss, f"ranged_attack_miss missing 'ac': {miss}"
            return
    pytest.skip("No seed produced a ranged_attack_miss in 50 attempts")


def test_ranged_miss_event_unchanged():
    """ranged_miss (no target) should have direction, no roll fields."""
    attacker = make_bot(emoji="A", x=5, y=5,
                        unlocked_actions=["move", "attack", "rest", "defend", "ranged_attack"])
    # No target 2 squares north
    actions = {"A": ("ranged_attack", "north")}
    events = resolve_ranged_attacks([attacker], actions)
    misses = [e for e in events if e["type"] == "ranged_miss"]
    assert len(misses) == 1, f"Expected 1 ranged_miss, got {events}"
    miss = misses[0]
    assert "direction" in miss
    assert "roll" not in miss, "ranged_miss should NOT have roll data"
