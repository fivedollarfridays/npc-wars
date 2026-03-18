"""Tests for Bot dict serialization and damage calculation."""

from tests.conftest import make_bot

from engine.combat import (
    DEFEND_BONUS,
    STARTING_ATTACK_POWER,
    calculate_damage,
)


# --- Dict serialization ---


class TestDictSerialization:
    def test_enemy_dict_keys(self):
        d = make_bot(name="A", emoji="🅰️", x=3, y=4, hp=80).to_enemy_dict()
        assert set(d.keys()) == {"name", "emoji", "x", "y", "hp", "score", "momentum_tier"}

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
            "momentum_tier", "momentum_name",
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
