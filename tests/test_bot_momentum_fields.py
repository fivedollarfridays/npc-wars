"""Tests for momentum fields in Bot state dicts."""

from engine.combat import Bot


def _make_bot(**kwargs) -> Bot:
    defaults = dict(
        name="Test", emoji="\U0001f916", bio="test", author="t",
        decide_func=lambda s: ("rest",), x=5, y=5,
    )
    defaults.update(kwargs)
    return Bot(**defaults)


class TestBotSelfDict:
    """to_self_dict includes momentum fields."""

    def test_self_dict_has_momentum_tier(self):
        bot = _make_bot()
        d = bot.to_self_dict()
        assert "momentum_tier" in d

    def test_self_dict_momentum_tier_default(self):
        bot = _make_bot()
        assert bot.to_self_dict()["momentum_tier"] == 0

    def test_self_dict_has_momentum_name(self):
        bot = _make_bot()
        assert "momentum_name" in bot.to_self_dict()

    def test_self_dict_momentum_name_default(self):
        bot = _make_bot()
        # Tier 0 name is empty string
        assert bot.to_self_dict()["momentum_name"] == ""

    def test_self_dict_reflects_score_based_name(self):
        bot = _make_bot()
        bot.score = 25  # Tier 2 threshold
        bot.momentum_tier = 2
        d = bot.to_self_dict()
        assert d["momentum_tier"] == 2
        assert d["momentum_name"] == "Battle Fury"


class TestBotEnemyDict:
    """to_enemy_dict includes momentum_tier (visible to opponents)."""

    def test_enemy_dict_has_momentum_tier(self):
        bot = _make_bot()
        assert "momentum_tier" in bot.to_enemy_dict()

    def test_enemy_dict_momentum_tier_default(self):
        bot = _make_bot()
        assert bot.to_enemy_dict()["momentum_tier"] == 0

    def test_enemy_dict_reflects_set_value(self):
        bot = _make_bot()
        bot.momentum_tier = 2
        assert bot.to_enemy_dict()["momentum_tier"] == 2
