"""Tests for the passivity plague — progressive penalty for not engaging."""

from tests.conftest import make_bot
from engine.plague import (
    PLAGUE_GRACE_ROUNDS, is_active_action, apply_plague, update_passivity,
)


class TestIsActiveAction:
    """Determine which actions count as 'engaging'."""

    def test_attack_is_active(self):
        bot = make_bot(x=5, y=5)
        enemies = [{"x": 5, "y": 4}]
        assert is_active_action(("attack", "north"), bot, enemies)

    def test_defend_with_nearby_enemy_is_active(self):
        bot = make_bot(x=5, y=5)
        enemies = [{"x": 5, "y": 3}]  # 2 tiles
        assert is_active_action(("defend",), bot, enemies)

    def test_defend_far_from_enemies_is_passive(self):
        bot = make_bot(x=5, y=5)
        enemies = [{"x": 0, "y": 0}]  # far
        assert not is_active_action(("defend",), bot, enemies)

    def test_move_toward_enemy_is_active(self):
        bot = make_bot(x=5, y=5)
        enemies = [{"x": 5, "y": 2}]  # north
        assert is_active_action(("move", "north"), bot, enemies)

    def test_move_away_from_enemy_is_passive(self):
        bot = make_bot(x=5, y=5)
        enemies = [{"x": 5, "y": 2}]  # north
        assert not is_active_action(("move", "south"), bot, enemies)

    def test_rest_is_passive(self):
        bot = make_bot(x=5, y=5)
        enemies = [{"x": 5, "y": 4}]
        assert not is_active_action(("rest",), bot, enemies)

    def test_taunt_is_active(self):
        bot = make_bot(x=5, y=5)
        enemies = [{"x": 5, "y": 4}]
        assert is_active_action(("taunt",), bot, enemies)

    def test_ranged_attack_is_active(self):
        bot = make_bot(x=5, y=5)
        enemies = [{"x": 5, "y": 3}]
        assert is_active_action(("ranged_attack", "north"), bot, enemies)


class TestUpdatePassivity:
    """Track consecutive passive rounds."""

    def test_active_resets_counter(self):
        bot = make_bot()
        bot.passive_rounds = 5
        update_passivity(bot, is_active=True)
        assert bot.passive_rounds == 0

    def test_passive_increments(self):
        bot = make_bot()
        bot.passive_rounds = 3
        update_passivity(bot, is_active=False)
        assert bot.passive_rounds == 4

    def test_starts_at_zero(self):
        bot = make_bot()
        assert bot.passive_rounds == 0


class TestApplyPlague:
    """Progressive penalties after grace period."""

    def test_no_penalty_during_grace(self):
        bot = make_bot(hp=100)
        bot.passive_rounds = PLAGUE_GRACE_ROUNDS - 1
        events = apply_plague(bot)
        assert bot.hp == 100
        assert len(events) == 0

    def test_energy_drain_after_grace(self):
        bot = make_bot(hp=100, energy=80)
        bot.passive_rounds = PLAGUE_GRACE_ROUNDS
        apply_plague(bot)
        assert bot.energy < 80

    def test_hp_damage_escalates(self):
        bot1 = make_bot(hp=100)
        bot1.passive_rounds = PLAGUE_GRACE_ROUNDS + 2
        apply_plague(bot1)

        bot2 = make_bot(hp=100)
        bot2.passive_rounds = PLAGUE_GRACE_ROUNDS + 6
        apply_plague(bot2)

        assert bot2.hp < bot1.hp  # more passive = more damage

    def test_plague_event_emitted(self):
        bot = make_bot(hp=100, energy=80)
        bot.passive_rounds = PLAGUE_GRACE_ROUNDS + 2
        events = apply_plague(bot)
        assert len(events) >= 1
        assert events[0]["type"] == "plague"
        assert "emoji" in events[0]

    def test_plague_leaves_1hp_minimum(self):
        bot = make_bot(hp=5, energy=5)
        bot.passive_rounds = PLAGUE_GRACE_ROUNDS + 15
        apply_plague(bot)
        assert bot.hp >= 1

    def test_dead_bots_not_affected(self):
        bot = make_bot(hp=0)
        bot.alive = False
        bot.passive_rounds = 20
        events = apply_plague(bot)
        assert len(events) == 0
