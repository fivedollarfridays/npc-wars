"""Tests for ranged attack action — validation, resolution, damage, energy cost."""

from engine.sandbox import validate_action
from engine.combat import ACTION_COSTS, RANGED_ATTACK_COST, RANGED_ATTACK_DAMAGE
from engine.rounds import resolve_ranged_attacks
from tests.conftest import make_bot


class TestRangedAttackValidation:
    def test_valid_ranged_attack_north(self):
        assert validate_action(("ranged_attack", "north")) == ("ranged_attack", "north")

    def test_valid_ranged_attack_all_directions(self):
        for d in ("north", "south", "east", "west"):
            assert validate_action(("ranged_attack", d)) == ("ranged_attack", d)

    def test_invalid_direction_rejected(self):
        assert validate_action(("ranged_attack", "invalid_dir")) is None

    def test_missing_direction_rejected(self):
        assert validate_action(("ranged_attack",)) is None


class TestResolveRangedAttacksHitMiss:
    def test_hits_bot_at_distance_2(self):
        """Ranged attack north should hit bot exactly 2 tiles away."""
        attacker = make_bot(emoji="A", x=5, y=5)
        target = make_bot(emoji="T", x=5, y=3)  # 2 north
        actions = {"A": ("ranged_attack", "north")}
        events = resolve_ranged_attacks([attacker, target], actions)
        hit_events = [e for e in events if e["type"] == "ranged_hit"]
        assert len(hit_events) == 1
        assert hit_events[0]["attacker"] == "A"
        assert hit_events[0]["target"] == "T"
        assert hit_events[0]["damage"] == 15

    def test_miss_when_no_bot_at_distance_2(self):
        """Ranged attack misses when no bot at target tile."""
        attacker = make_bot(emoji="A", x=5, y=5)
        actions = {"A": ("ranged_attack", "north")}
        events = resolve_ranged_attacks([attacker], actions)
        miss_events = [e for e in events if e["type"] == "ranged_miss"]
        assert len(miss_events) == 1
        assert miss_events[0]["attacker"] == "A"

    def test_does_not_hit_bot_at_distance_1(self):
        """Ranged attack should NOT hit a bot only 1 tile away."""
        attacker = make_bot(emoji="A", x=5, y=5)
        adjacent = make_bot(emoji="T", x=5, y=4)  # 1 north
        actions = {"A": ("ranged_attack", "north")}
        events = resolve_ranged_attacks([attacker, adjacent], actions)
        hit_events = [e for e in events if e["type"] == "ranged_hit"]
        assert len(hit_events) == 0
        miss_events = [e for e in events if e["type"] == "ranged_miss"]
        assert len(miss_events) == 1

    def test_does_not_hit_bot_at_distance_3(self):
        """Ranged attack should NOT hit a bot 3 tiles away."""
        attacker = make_bot(emoji="A", x=5, y=5)
        far = make_bot(emoji="T", x=5, y=2)  # 3 north
        actions = {"A": ("ranged_attack", "north")}
        events = resolve_ranged_attacks([attacker, far], actions)
        hit_events = [e for e in events if e["type"] == "ranged_hit"]
        assert len(hit_events) == 0


class TestRangedAttackDamage:
    def test_damage_is_fixed_15_regardless_of_attack_power(self):
        """Ranged damage is flat 15, not scaled by attack_power."""
        attacker = make_bot(emoji="A", x=5, y=5, attack_power=50)
        target = make_bot(emoji="T", x=5, y=3)
        actions = {"A": ("ranged_attack", "north")}
        events = resolve_ranged_attacks([attacker, target], actions)
        hit_events = [e for e in events if e["type"] == "ranged_hit"]
        assert hit_events[0]["damage"] == 15

    def test_target_hp_reduced_by_15(self):
        """Target HP should decrease by exactly 15."""
        attacker = make_bot(emoji="A", x=5, y=5)
        target = make_bot(emoji="T", x=5, y=3, hp=100)
        actions = {"A": ("ranged_attack", "north")}
        resolve_ranged_attacks([attacker, target], actions)
        assert target.hp == 85


class TestRangedAttackEnergyCost:
    def test_ranged_attack_cost_constant(self):
        assert RANGED_ATTACK_COST == 20

    def test_ranged_attack_damage_constant(self):
        assert RANGED_ATTACK_DAMAGE == 15

    def test_action_costs_includes_ranged_attack(self):
        assert ACTION_COSTS["ranged_attack"] == 20
