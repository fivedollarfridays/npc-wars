"""Tests for situational to-hit modifiers (T29.3)."""

import random

from tests.conftest import make_bot
from engine.combat_rolls import roll_attack, roll_ranged_attack
from engine.stats import StatAllocation


# ---------------------------------------------------------------------------
# Cycle 1: to_hit_modifier param in roll_attack / roll_ranged_attack
# ---------------------------------------------------------------------------


def _make_derived(initiative: int = 25):
    """Create a bot and return its DerivedStats."""
    mind = 100 - 25 - initiative - 25
    alloc = StatAllocation(power=25, speed=initiative, armor=25, mind=mind)
    bot = make_bot(stat_allocation=alloc)
    return bot.derived


def test_to_hit_modifier_increases_hit_rate():
    """A +5 to-hit modifier should produce a higher hit rate than 0."""
    attacker = _make_derived()
    defender = _make_derived()
    n = 2000
    hits_base = sum(
        roll_attack(attacker, defender, rng=random.Random(i)).hit
        for i in range(n)
    )
    hits_bonus = sum(
        roll_attack(attacker, defender, rng=random.Random(i),
                    to_hit_modifier=5).hit
        for i in range(n)
    )
    assert hits_bonus > hits_base


def test_to_hit_modifier_negative_decreases_hit_rate():
    """A -5 to-hit modifier should produce a lower hit rate than 0."""
    attacker = _make_derived()
    defender = _make_derived()
    n = 2000
    hits_base = sum(
        roll_attack(attacker, defender, rng=random.Random(i)).hit
        for i in range(n)
    )
    hits_penalty = sum(
        roll_attack(attacker, defender, rng=random.Random(i),
                    to_hit_modifier=-5).hit
        for i in range(n)
    )
    assert hits_penalty < hits_base


def test_to_hit_modifier_added_to_result_modifier():
    """CombatResult.modifier should include to_hit_modifier."""
    attacker = _make_derived(initiative=30)
    defender = _make_derived()
    result = roll_attack(attacker, defender, rng=random.Random(1),
                         to_hit_modifier=4)
    # initiative // 10 = 3, + 4 = 7
    assert result.modifier == 7


def test_ranged_to_hit_modifier():
    """roll_ranged_attack should also accept to_hit_modifier."""
    attacker = _make_derived()
    defender = _make_derived()
    n = 2000
    hits_base = sum(
        roll_ranged_attack(attacker, defender, rng=random.Random(i)).hit
        for i in range(n)
    )
    hits_bonus = sum(
        roll_ranged_attack(attacker, defender, rng=random.Random(i),
                           to_hit_modifier=5).hit
        for i in range(n)
    )
    assert hits_bonus > hits_base


def test_modifier_constants_exported():
    """REST_HIT_BONUS and TAUNT_HIT_PENALTY importable from combat_rolls."""
    from engine.combat_rolls import REST_HIT_BONUS, TAUNT_HIT_PENALTY
    assert REST_HIT_BONUS == 3
    assert TAUNT_HIT_PENALTY == 3


# ---------------------------------------------------------------------------
# Cycle 2: Situational modifiers in _roll_melee / _roll_ranged
# ---------------------------------------------------------------------------


def test_resting_target_hit_rate_higher():
    """Resting target should be hit more often (+3 bonus)."""
    from engine.rounds_combat import resolve_attacks, build_pos_map

    attacker = make_bot(emoji="A", x=5, y=5)
    # Target adjacent north
    target = make_bot(emoji="B", x=5, y=4)

    n = 1000
    hits_rest = 0
    hits_defend = 0
    for i in range(n):
        # Reset HP
        attacker.hp = attacker.derived.max_hp
        target.hp = target.derived.max_hp
        actions_rest = {"A": ("attack", "north"), "B": ("rest",)}
        bots = [attacker, target]
        events = resolve_attacks(bots, actions_rest,
                                 pos_map=build_pos_map(bots),
                                 rng=random.Random(i))
        if events and events[0].get("type") == "hit":
            hits_rest += 1

        attacker.hp = attacker.derived.max_hp
        target.hp = target.derived.max_hp
        actions_idle = {"A": ("attack", "north")}
        events2 = resolve_attacks(bots, actions_idle,
                                  pos_map=build_pos_map(bots),
                                  rng=random.Random(i))
        if events2 and events2[0].get("type") == "hit":
            hits_defend += 1

    assert hits_rest > hits_defend, f"Resting: {hits_rest}, no action: {hits_defend}"


def test_taunted_penalty_vs_non_taunter():
    """Taunted bot attacking non-taunter should have lower hit rate."""
    from engine.rounds_combat import resolve_attacks, build_pos_map

    n = 1000
    hits_taunted = 0
    hits_normal = 0
    for i in range(n):
        attacker = make_bot(emoji="A", x=5, y=5)
        target = make_bot(emoji="B", x=5, y=4)

        # Taunted: attacking B but taunted by C
        attacker.taunt_target = "C"
        actions = {"A": ("attack", "north"), "B": ("rest",)}
        bots = [attacker, target]
        events = resolve_attacks(bots, actions,
                                 pos_map=build_pos_map(bots),
                                 rng=random.Random(i))
        if events and events[0].get("type") == "hit":
            hits_taunted += 1

        # Normal: no taunt
        attacker2 = make_bot(emoji="A", x=5, y=5)
        target2 = make_bot(emoji="B", x=5, y=4)
        actions2 = {"A": ("attack", "north"), "B": ("rest",)}
        bots2 = [attacker2, target2]
        events2 = resolve_attacks(bots2, actions2,
                                  pos_map=build_pos_map(bots2),
                                  rng=random.Random(i))
        if events2 and events2[0].get("type") == "hit":
            hits_normal += 1

    assert hits_taunted < hits_normal, f"Taunted: {hits_taunted}, Normal: {hits_normal}"


def test_taunted_no_penalty_vs_taunter():
    """Taunted bot attacking its taunter should have no penalty."""
    from engine.rounds_combat import resolve_attacks, build_pos_map

    n = 1000
    hits_vs_taunter = 0
    hits_normal = 0
    for i in range(n):
        attacker = make_bot(emoji="A", x=5, y=5)
        target = make_bot(emoji="B", x=5, y=4)

        # Taunted by B, attacking B — no penalty
        attacker.taunt_target = "B"
        actions = {"A": ("attack", "north")}
        bots = [attacker, target]
        events = resolve_attacks(bots, actions,
                                 pos_map=build_pos_map(bots),
                                 rng=random.Random(i))
        if events and events[0].get("type") == "hit":
            hits_vs_taunter += 1

        # No taunt — same hit rate expected
        attacker2 = make_bot(emoji="A", x=5, y=5)
        target2 = make_bot(emoji="B", x=5, y=4)
        actions2 = {"A": ("attack", "north")}
        bots2 = [attacker2, target2]
        events2 = resolve_attacks(bots2, actions2,
                                  pos_map=build_pos_map(bots2),
                                  rng=random.Random(i))
        if events2 and events2[0].get("type") == "hit":
            hits_normal += 1

    # Should be identical since same RNG seeds and no penalty
    assert hits_vs_taunter == hits_normal


def test_modifiers_stack_to_zero():
    """Taunted attacking resting non-taunter: +3 -3 = net 0."""
    from engine.rounds_combat import resolve_attacks, build_pos_map

    n = 1000
    hits_stacked = 0
    hits_normal = 0
    for i in range(n):
        # Stacked: rest bonus + taunt penalty = 0
        attacker = make_bot(emoji="A", x=5, y=5)
        target = make_bot(emoji="B", x=5, y=4)
        attacker.taunt_target = "C"
        actions = {"A": ("attack", "north"), "B": ("rest",)}
        bots = [attacker, target]
        events = resolve_attacks(bots, actions,
                                 pos_map=build_pos_map(bots),
                                 rng=random.Random(i))
        if events and events[0].get("type") == "hit":
            hits_stacked += 1

        # Normal: no rest, no taunt
        attacker2 = make_bot(emoji="A", x=5, y=5)
        target2 = make_bot(emoji="B", x=5, y=4)
        actions2 = {"A": ("attack", "north")}
        bots2 = [attacker2, target2]
        events2 = resolve_attacks(bots2, actions2,
                                  pos_map=build_pos_map(bots2),
                                  rng=random.Random(i))
        if events2 and events2[0].get("type") == "hit":
            hits_normal += 1

    assert hits_stacked == hits_normal


def test_no_taunt_no_penalty():
    """Bot without taunt_target has no penalty."""
    attacker = make_bot(emoji="A", x=5, y=5)
    assert attacker.taunt_target is None
    # Just verify the attribute exists and is None — no penalty case
    # is implicitly tested by all normal attack tests
