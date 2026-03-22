"""Tests for Bot dict serialization and damage calculation."""

from tests.conftest import make_bot

from engine.combat import (
    DEFEND_BONUS,
    STARTING_ATTACK_POWER,
    calculate_damage,
)
from engine.stats import StatAllocation, calculate_derived


# --- Dict serialization ---


class TestDictSerialization:
    def test_enemy_dict_keys(self):
        d = make_bot(name="A", emoji="🅰️", x=3, y=4, hp=80).to_enemy_dict()
        assert set(d.keys()) == {
            "name", "emoji", "x", "y", "hp", "score",
            "momentum_tier", "is_leader", "max_hp", "speed_class", "glyph",
            "has_traps", "trap_count", "weapon", "armor", "has_ability",
        }

    def test_enemy_dict_hides_energy(self):
        d = make_bot().to_enemy_dict()
        assert "energy" not in d

    def test_enemy_dict_values(self):
        d = make_bot(name="A", emoji="🅰️", x=3, y=4, hp=80).to_enemy_dict()
        assert d["name"] == "A"
        assert d["emoji"] == "🅰️"
        assert d["x"] == 3
        assert d["y"] == 4
        assert d["hp"] == 80

    def test_self_dict_keys(self):
        d = make_bot().to_self_dict()
        assert set(d.keys()) == {
            "x", "y", "hp", "energy", "attack_power", "defense",
            "unlocked_actions", "line_budget", "win_streak", "score",
            "momentum_tier", "momentum_name", "is_leader",
            "power", "speed", "armor", "mind",
            "max_hp", "max_energy", "min_damage", "max_damage",
            "dodge_chance", "damage_reduction", "glyph",
            "passive_rounds", "traps", "trap_cooldown", "callbacks",
            "equipment", "equipment_bonuses",
            "ability", "tactical_cooldown",
        }

    def test_self_dict_includes_energy(self):
        d = make_bot(energy=42).to_self_dict()
        assert d["energy"] == 42

    def test_self_dict_values(self):
        bot = make_bot(x=2, y=3, hp=75, energy=60)
        bot.defense = DEFEND_BONUS
        d = bot.to_self_dict()
        assert d["x"] == 2
        assert d["y"] == 3
        assert d["hp"] == 75
        assert d["energy"] == 60
        assert d["attack_power"] == STARTING_ATTACK_POWER
        assert d["defense"] == DEFEND_BONUS

    def test_self_dict_has_stat_fields(self):
        alloc = StatAllocation(power=30, speed=20, armor=30, mind=20)
        d = make_bot(stat_allocation=alloc).to_self_dict()
        assert d["power"] == 30
        assert d["speed"] == 20
        assert d["armor"] == 30
        assert d["mind"] == 20

    def test_self_dict_has_derived_fields(self):
        d = make_bot().to_self_dict()
        # Default 25/25/25/25 derived values (with versatility bonus)
        assert d["max_hp"] == 145
        assert d["max_energy"] == 100
        assert d["min_damage"] == 35
        assert d["max_damage"] == 55
        assert d["dodge_chance"] == 7.5
        assert d["damage_reduction"] == 0

    def test_enemy_dict_has_max_hp(self):
        alloc = StatAllocation(power=20, speed=20, armor=40, mind=20)
        d = make_bot(stat_allocation=alloc).to_enemy_dict()
        assert d["max_hp"] == calculate_derived(alloc).max_hp

    def test_enemy_dict_has_speed_class(self):
        d = make_bot().to_enemy_dict()
        assert "speed_class" in d

    def test_enemy_dict_default_speed_class_normal(self):
        # default speed=25 -> "normal"
        d = make_bot().to_enemy_dict()
        assert d["speed_class"] == "normal"

    def test_enemy_dict_speed_class_slow(self):
        alloc = StatAllocation(power=35, speed=10, armor=30, mind=25)
        d = make_bot(stat_allocation=alloc).to_enemy_dict()
        assert d["speed_class"] == "slow"

    def test_enemy_dict_speed_class_fast(self):
        alloc = StatAllocation(power=15, speed=40, armor=20, mind=25)
        d = make_bot(stat_allocation=alloc).to_enemy_dict()
        assert d["speed_class"] == "fast"

    def test_enemy_dict_speed_class_blazing(self):
        alloc = StatAllocation(power=10, speed=50, armor=15, mind=25)
        d = make_bot(stat_allocation=alloc).to_enemy_dict()
        assert d["speed_class"] == "blazing"


# --- calculate_damage ---


class TestCalculateDamage:
    def test_undefended_full_damage(self):
        attacker = make_bot()
        defender = make_bot()
        assert calculate_damage(attacker, defender) == STARTING_ATTACK_POWER

    def test_defended_reduces_damage(self):
        attacker = make_bot()
        defender = make_bot()
        defender.defense = DEFEND_BONUS
        assert calculate_damage(attacker, defender) == STARTING_ATTACK_POWER - DEFEND_BONUS

    def test_defense_exceeds_attack_zero_damage(self):
        attacker = make_bot()
        defender = make_bot()
        defender.defense = STARTING_ATTACK_POWER + 5
        assert calculate_damage(attacker, defender) == 0

    def test_defense_equals_attack_zero_damage(self):
        attacker = make_bot()
        defender = make_bot()
        defender.defense = STARTING_ATTACK_POWER
        assert calculate_damage(attacker, defender) == 0
