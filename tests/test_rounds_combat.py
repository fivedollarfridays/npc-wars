"""Tests for engine/rounds_combat.py — verifies extract-and-move refactor."""

import random

from tests.conftest import make_bot


def test_resolve_attacks_importable_from_rounds_combat():
    """resolve_attacks can be imported from the new module."""
    from engine.rounds_combat import resolve_attacks
    assert callable(resolve_attacks)


def test_resolve_attacks_importable_from_rounds():
    """resolve_attacks is still importable from engine.rounds (backward compat)."""
    from engine.rounds import resolve_attacks
    assert callable(resolve_attacks)


def test_build_pos_map_importable_from_both():
    """build_pos_map importable from both rounds and rounds_combat."""
    from engine.rounds_combat import build_pos_map as from_combat
    from engine.rounds import build_pos_map as from_rounds
    assert from_combat is from_rounds


def test_resolve_ranged_attacks_importable_from_both():
    """resolve_ranged_attacks importable from both modules."""
    from engine.rounds_combat import resolve_ranged_attacks as from_combat
    from engine.rounds import resolve_ranged_attacks as from_rounds
    assert from_combat is from_rounds


def test_resolve_attacks_with_rng_works():
    """Basic melee attack through rounds_combat with rng produces events."""
    from engine.rounds_combat import resolve_attacks, build_pos_map

    attacker = make_bot(name="Attacker", emoji="A", hp=100, energy=100, x=2, y=3)
    target = make_bot(name="Target", emoji="T", hp=100, energy=100, x=3, y=3)

    alive = [attacker, target]
    actions = {"A": ("attack", "east"), "T": ("rest",)}
    pos_map = build_pos_map(alive)
    rng = random.Random(42)

    events = resolve_attacks(alive, actions, pos_map=pos_map, rng=rng)

    # Should produce exactly one event (hit or attack_miss)
    assert len(events) == 1
    evt = events[0]
    assert evt["attacker"] == "A"
    assert evt["type"] in ("hit", "attack_miss")
