"""Tests for initiative system — SPEED-based attack ordering."""

import random

from tests.conftest import make_bot
from engine.rounds_combat import resolve_attacks, resolve_ranged_attacks
from engine.stats import StatAllocation


def _fast_slow_bots():
    """Create a fast bot (SPEED=50) and slow bot (SPEED=10), facing each other."""
    fast = make_bot(
        name="Fast", emoji="F", x=5, y=5,
        stat_allocation=StatAllocation(20, 50, 15, 15),
    )
    slow = make_bot(
        name="Slow", emoji="S", x=5, y=4,
        stat_allocation=StatAllocation(20, 10, 50, 20),
    )
    return fast, slow


# --- Cycle 1: ordering ---

def test_higher_speed_attacks_first():
    """Fast bot's attack event should appear before slow bot's event."""
    fast, slow = _fast_slow_bots()
    actions = {"F": ("attack", "north"), "S": ("attack", "south")}
    # Slow listed first in input, but fast should resolve first
    events = resolve_attacks([slow, fast], actions, rng=random.Random(42))
    attackers = [e["attacker"] for e in events if "attacker" in e]
    assert attackers[0] == "F", f"Expected fast bot first, got {attackers}"


def test_equal_speed_preserves_order():
    """Bots with equal SPEED keep their original list order (stable sort)."""
    a = make_bot(name="A", emoji="A", x=3, y=3)
    b = make_bot(name="B", emoji="B", x=3, y=4)
    c = make_bot(name="C", emoji="C", x=3, y=2)
    # Place targets for each attacker
    target_a = make_bot(name="TA", emoji="X", x=3, y=2)
    target_b = make_bot(name="TB", emoji="Y", x=3, y=5)
    target_c = make_bot(name="TC", emoji="Z", x=3, y=1)
    actions = {
        "A": ("attack", "north"),
        "B": ("attack", "south"),
        "C": ("attack", "north"),
    }
    all_bots = [a, b, c, target_a, target_b, target_c]
    events = resolve_attacks(all_bots, actions, rng=random.Random(99))
    attackers = [e["attacker"] for e in events if "attacker" in e]
    assert attackers == ["A", "B", "C"], f"Expected stable order, got {attackers}"


# --- Cycle 2: mid-round kill prevention ---

def test_fast_bot_prevents_dead_bot_attack():
    """If fast bot kills slow bot, slow bot should not get an attack event."""
    fast, slow = _fast_slow_bots()
    # Give slow bot very low HP so fast bot can one-shot via flat damage (25)
    slow.hp = 1
    actions = {"F": ("attack", "north"), "S": ("attack", "south")}
    # Use rng=None (flat damage path) to guarantee a hit
    events = resolve_attacks([slow, fast], actions, rng=None)
    attackers = [e["attacker"] for e in events if "attacker" in e]
    assert "S" not in attackers, f"Dead bot should not attack, got {attackers}"


# --- Cycle 3: ranged attacks ---

def test_ranged_also_sorted_by_initiative():
    """Ranged attacks should also resolve in initiative order."""
    fast = make_bot(
        name="Fast", emoji="F", x=5, y=5,
        stat_allocation=StatAllocation(20, 50, 15, 15),
    )
    slow = make_bot(
        name="Slow", emoji="S", x=5, y=3,
        stat_allocation=StatAllocation(20, 10, 50, 20),
    )
    # Targets at range 2 from each shooter
    target_f = make_bot(name="TF", emoji="X", x=5, y=3)
    target_s = make_bot(name="TS", emoji="Y", x=5, y=5)
    actions = {"F": ("ranged_attack", "north"), "S": ("ranged_attack", "south")}
    all_bots = [slow, fast, target_f, target_s]
    events = resolve_ranged_attacks(all_bots, actions, rng=random.Random(42))
    attackers = [e["attacker"] for e in events if "attacker" in e]
    assert attackers[0] == "F", f"Expected fast bot first in ranged, got {attackers}"


def test_ranged_fast_kill_prevents_slow_attack():
    """Ranged: if fast bot kills slow bot at range, slow bot doesn't shoot."""
    fast = make_bot(
        name="Fast", emoji="F", x=5, y=5,
        stat_allocation=StatAllocation(20, 50, 15, 15),
    )
    slow = make_bot(
        name="Slow", emoji="S", x=5, y=3,
        stat_allocation=StatAllocation(20, 10, 50, 20),
    )
    slow.hp = 1  # one-shot threshold
    # Fast shoots north at slow (range 2: 5,5 -> 5,4 -> 5,3)
    # Slow shoots south at fast (range 2: 5,3 -> 5,4 -> 5,5)
    actions = {"F": ("ranged_attack", "north"), "S": ("ranged_attack", "south")}
    all_bots = [slow, fast]
    # Use rng=None (flat damage path) to guarantee a hit
    events = resolve_ranged_attacks(all_bots, actions, rng=None)
    attackers = [e["attacker"] for e in events if "attacker" in e]
    assert "S" not in attackers, f"Dead bot should not ranged attack, got {attackers}"


# --- Cycle 4: backward compatibility ---

def test_default_stats_no_behavior_change():
    """At default 25/25/25/25, all bots have equal initiative — stable order preserved."""
    a = make_bot(name="A", emoji="A", x=3, y=3)
    b = make_bot(name="B", emoji="B", x=3, y=4)
    target_a = make_bot(name="TA", emoji="X", x=3, y=2)
    target_b = make_bot(name="TB", emoji="Y", x=3, y=5)
    actions = {"A": ("attack", "north"), "B": ("attack", "south")}
    all_bots = [a, b, target_a, target_b]
    events = resolve_attacks(all_bots, actions, rng=random.Random(42))
    attackers = [e["attacker"] for e in events if "attacker" in e]
    assert attackers == ["A", "B"], f"Default stats should preserve order, got {attackers}"
