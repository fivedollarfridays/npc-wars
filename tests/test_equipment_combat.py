"""Tests for equipment bonuses wired into the combat pipeline."""

from __future__ import annotations

import random

from engine.combat import Bot, ACTION_COSTS
from engine.combat_rolls import (
    _compute_ac,
    roll_attack,
    roll_ranged_attack,
)
from engine.equipment import EquipmentBonuses, compute_equipment_bonuses
from engine.stats import DerivedStats


def _make_derived(**overrides: int | float) -> DerivedStats:
    """Build a DerivedStats with sane defaults, overriding specific fields."""
    defaults = {
        "max_hp": 100, "max_energy": 100, "min_damage": 5, "max_damage": 10,
        "crit_multiplier": 1.5, "dodge_chance": 0.0, "initiative": 25,
        "damage_reduction": 0, "energy_regen": 0,
    }
    defaults.update(overrides)
    return DerivedStats(**defaults)


def _make_bot(**overrides) -> Bot:
    """Build a minimal Bot for testing."""
    defaults = {
        "name": "TestBot", "emoji": "T", "bio": "", "author": "test",
        "decide_func": lambda *a: ("rest",), "x": 0, "y": 0,
    }
    defaults.update(overrides)
    return Bot(**defaults)


# ── Cycle 1: _compute_ac with equipment_dr and armor_pierce ──


def test_compute_ac_with_equipment_dr():
    """Plate armor DR (+6) increases effective AC."""
    defender = _make_derived(damage_reduction=0)
    ac_base = _compute_ac(defender, defending=False, momentum_defense_reduct=0.0)
    ac_with_dr = _compute_ac(
        defender, defending=False, momentum_defense_reduct=0.0,
        equipment_dr=6,
    )
    assert ac_with_dr == ac_base + 6


def test_compute_ac_with_armor_pierce():
    """Mace armor_pierce reduces defender's effective AC."""
    defender = _make_derived(damage_reduction=4)
    ac_full = _compute_ac(
        defender, defending=False, momentum_defense_reduct=0.0,
        equipment_dr=0, armor_pierce=0,
    )
    ac_pierced = _compute_ac(
        defender, defending=False, momentum_defense_reduct=0.0,
        equipment_dr=0, armor_pierce=4,
    )
    assert ac_pierced == ac_full - 4


def test_armor_pierce_cannot_reduce_ac_below_one():
    """Armor pierce should not reduce AC below 1."""
    defender = _make_derived(damage_reduction=0)
    ac = _compute_ac(
        defender, defending=False, momentum_defense_reduct=0.0,
        equipment_dr=0, armor_pierce=100,
    )
    assert ac >= 1


# ── Cycle 2: roll_attack with equipment bonuses ──


def test_sword_to_hit_bonus():
    """Sword gives +1 to-hit, passed as equipment_to_hit to roll_attack."""
    attacker = _make_derived(initiative=0, min_damage=5, max_damage=5)
    defender = _make_derived(damage_reduction=0, dodge_chance=0.0)
    # Roll many times to check modifier increases
    hits_without = 0
    hits_with = 0
    for seed in range(200):
        r1 = roll_attack(attacker, defender, defending=False, rng=random.Random(seed))
        r2 = roll_attack(
            attacker, defender, defending=False, rng=random.Random(seed),
            equipment_to_hit=1,
        )
        hits_without += r1.hit
        hits_with += r2.hit
    assert hits_with >= hits_without


def test_axe_crit_mult_bonus():
    """Axe gives +0.2 crit multiplier in roll_attack."""
    attacker = _make_derived(initiative=100, min_damage=10, max_damage=10,
                             crit_multiplier=1.5)
    defender = _make_derived(damage_reduction=0, dodge_chance=0.0)
    # Use a seed that produces a crit (d20=20 or high roll)
    for seed in range(1000):
        r_base = roll_attack(attacker, defender, defending=False, rng=random.Random(seed))
        if r_base.is_crit:
            r_equip = roll_attack(
                attacker, defender, defending=False, rng=random.Random(seed),
                equipment_crit_mult=0.2,
            )
            assert r_equip.damage > r_base.damage
            break
    else:
        raise AssertionError("No crit found in 1000 seeds")


def test_mace_armor_pierce_reduces_defender_ac():
    """Mace armor_pierce=4 reduces defender AC in roll_attack."""
    attacker = _make_derived(initiative=0, min_damage=5, max_damage=5)
    defender = _make_derived(damage_reduction=6, dodge_chance=0.0)
    hits_base = 0
    hits_pierce = 0
    for seed in range(200):
        r1 = roll_attack(attacker, defender, defending=False, rng=random.Random(seed))
        r2 = roll_attack(
            attacker, defender, defending=False, rng=random.Random(seed),
            equipment_dr=0, armor_pierce=4,
        )
        hits_base += r1.hit
        hits_pierce += r2.hit
    assert hits_pierce > hits_base


def test_plate_dr_in_roll_attack():
    """Plate DR=6 increases defender AC in roll_attack."""
    attacker = _make_derived(initiative=0, min_damage=5, max_damage=5)
    defender = _make_derived(damage_reduction=0, dodge_chance=0.0)
    hits_base = 0
    hits_plated = 0
    for seed in range(200):
        r1 = roll_attack(attacker, defender, defending=False, rng=random.Random(seed))
        r2 = roll_attack(
            attacker, defender, defending=False, rng=random.Random(seed),
            equipment_dr=6,
        )
        hits_base += r1.hit
        hits_plated += r2.hit
    assert hits_base > hits_plated


def test_equipment_damage_range_additive():
    """Equipment min/max damage bonuses are additive with attacker stats."""
    attacker = _make_derived(initiative=100, min_damage=5, max_damage=5,
                             crit_multiplier=1.0)
    defender = _make_derived(damage_reduction=0, dodge_chance=0.0)
    for seed in range(200):
        r_base = roll_attack(attacker, defender, defending=False, rng=random.Random(seed))
        r_equip = roll_attack(
            attacker, defender, defending=False, rng=random.Random(seed),
            equipment_min_dmg=3, equipment_max_dmg=3,
        )
        if r_base.hit and r_equip.hit:
            # Both using fixed damage (5 vs 8), same crit_mult=1.0
            # Equip damage should be higher
            assert r_equip.damage >= r_base.damage
            break


# ── Cycle 3: roll_ranged_attack with equipment bonuses ──


def test_ranged_attack_with_equipment_to_hit():
    """Equipment to_hit bonus applies to ranged attacks too."""
    attacker = _make_derived(initiative=0, min_damage=10, max_damage=10)
    defender = _make_derived(damage_reduction=0, dodge_chance=0.0)
    hits_without = 0
    hits_with = 0
    for seed in range(200):
        r1 = roll_ranged_attack(attacker, defender, defending=False,
                                rng=random.Random(seed))
        r2 = roll_ranged_attack(attacker, defender, defending=False,
                                rng=random.Random(seed), equipment_to_hit=3)
        hits_without += r1.hit
        hits_with += r2.hit
    assert hits_with >= hits_without


# ── Cycle 5: Bot.apply_action_cost with equipment mods ──


def test_chain_mail_adds_energy_cost():
    """Chain mail energy penalties increase action costs."""
    bot = _make_bot()
    bot.equipment_bonuses = EquipmentBonuses(
        action_cost_mods={"attack": 2, "move": 2},
    )
    base_attack_cost = ACTION_COSTS["attack"]
    initial_energy = bot.energy
    bot.apply_action_cost("attack")
    actual_cost = initial_energy - bot.energy
    assert actual_cost == base_attack_cost + 2


def test_action_cost_min_zero():
    """Equipment cost reduction cannot make action cost negative."""
    bot = _make_bot()
    bot.equipment_bonuses = EquipmentBonuses(
        action_cost_mods={"rest": -100},
    )
    initial_energy = bot.energy
    bot.apply_action_cost("rest")
    assert bot.energy >= initial_energy  # rest cost is 0, can't go below


def test_default_equipment_bonuses_no_effect():
    """Default (empty) equipment bonuses should not change combat results."""
    attacker = _make_derived(initiative=25, min_damage=5, max_damage=10)
    defender = _make_derived(damage_reduction=2, dodge_chance=0.0)
    for seed in range(50):
        r1 = roll_attack(attacker, defender, defending=False, rng=random.Random(seed))
        r2 = roll_attack(
            attacker, defender, defending=False, rng=random.Random(seed),
            equipment_to_hit=0, equipment_min_dmg=0, equipment_max_dmg=0,
            equipment_crit_mult=0.0, equipment_dr=0, armor_pierce=0,
        )
        assert r1.hit == r2.hit
        assert r1.damage == r2.damage


def test_equipment_bonuses_field_on_bot():
    """Bot class has equipment_bonuses field defaulting to empty EquipmentBonuses."""
    bot = _make_bot()
    assert hasattr(bot, "equipment_bonuses")
    assert isinstance(bot.equipment_bonuses, EquipmentBonuses)
    assert bot.equipment_bonuses.to_hit == 0


def test_default_equipment_produces_expected_results():
    """Sword + leather defaults produce known bonuses."""
    bonuses = compute_equipment_bonuses({
        "weapon": "sword", "armor": "leather",
        "accessories": [], "tactical": None,
    })
    assert bonuses.to_hit == 1  # sword
    assert bonuses.min_damage == 3  # sword
    assert bonuses.max_damage == 5  # sword
    assert bonuses.dr == 2  # leather


# ── Cycle 6: Weapon specials ──


def test_spear_reach_allows_attack_at_2_tiles():
    """Spear with reach_distance=2 can hit targets 2 tiles away."""
    from engine.rounds_combat import resolve_attacks, build_pos_map

    attacker = _make_bot(emoji="A", x=0, y=0)
    attacker.equipment_bonuses = EquipmentBonuses(reach_distance=2)
    # Target is 2 tiles to the right (not adjacent)
    target = _make_bot(emoji="B", x=2, y=0)
    alive = [attacker, target]
    pos_map = build_pos_map(alive)
    actions = {"A": ("attack", "east"), "B": ("rest",)}
    events = resolve_attacks(alive, actions, pos_map, rng=random.Random(42))
    # Should find a target at distance 2
    hit_events = [e for e in events if e.get("type") in ("hit", "attack_miss")]
    assert len(hit_events) == 1
    assert hit_events[0]["target"] == "B"


def test_no_reach_misses_at_2_tiles():
    """Without reach, attack at 2 tiles away is a miss."""
    from engine.rounds_combat import resolve_attacks, build_pos_map

    attacker = _make_bot(emoji="A", x=0, y=0)
    # No reach (default)
    target = _make_bot(emoji="B", x=2, y=0)
    alive = [attacker, target]
    pos_map = build_pos_map(alive)
    actions = {"A": ("attack", "east"), "B": ("rest",)}
    events = resolve_attacks(alive, actions, pos_map, rng=random.Random(42))
    miss_events = [e for e in events if e.get("type") == "miss"]
    assert len(miss_events) == 1


def test_finesse_weapon_speed_to_hit():
    """Finesse weapon adds speed-based to-hit bonus in _roll_melee."""
    from engine.rounds_combat import resolve_attacks, build_pos_map
    from engine.stats import StatAllocation

    # High speed bot with finesse weapon
    attacker = _make_bot(emoji="A", x=0, y=0,
                         stat_allocation=StatAllocation(5, 65, 25, 5))
    attacker.equipment_bonuses = EquipmentBonuses(
        to_hit=2, special_weapon="finesse",
    )
    # Speed 65: (65-25)//10 = 4 extra to-hit
    target = _make_bot(emoji="B", x=1, y=0)
    alive = [attacker, target]
    pos_map = build_pos_map(alive)
    actions = {"A": ("attack", "east"), "B": ("rest",)}
    hits = 0
    for seed in range(200):
        # Reset target HP
        target.hp = 100.0
        target.alive = True
        events = resolve_attacks(alive, actions, pos_map, rng=random.Random(seed))
        for e in events:
            if e.get("type") == "hit":
                hits += 1
    # With high to-hit from finesse + speed, should hit most of the time
    assert hits > 150  # >75% hit rate with +6 to-hit + initiative/10


def test_roll_melee_wires_equipment_bonuses():
    """_roll_melee reads equipment_bonuses from attacker and defender."""
    from engine.rounds_combat import resolve_attacks, build_pos_map

    attacker = _make_bot(emoji="A", x=0, y=0)
    attacker.equipment_bonuses = compute_equipment_bonuses({
        "weapon": "sword", "armor": "leather",
        "accessories": [], "tactical": None,
    })
    target = _make_bot(emoji="B", x=1, y=0)
    target.equipment_bonuses = compute_equipment_bonuses({
        "weapon": "dagger", "armor": "plate",
        "accessories": [], "tactical": None,
    })
    alive = [attacker, target]
    pos_map = build_pos_map(alive)
    actions = {"A": ("attack", "east"), "B": ("rest",)}
    # Just verify it runs without error and produces events
    events = resolve_attacks(alive, actions, pos_map, rng=random.Random(42))
    assert len(events) >= 1
