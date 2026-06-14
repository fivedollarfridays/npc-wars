"""Tests for trap and callback state dict exposure."""

from __future__ import annotations

from engine.combat import Bot
from engine.traps import TrapManager
from engine.callbacks import CallbackSet


def _bot(emoji: str = "🤖", x: int = 3, y: int = 3) -> Bot:
    bot = Bot(
        name="Test", emoji=emoji, bio="test", author="test",
        decide_func=lambda s: ("rest",), x=x, y=y,
    )
    # T73.5: trap info is only exposed to bots that have unlocked `trap`.
    # These tests cover the placing bot, so unlock it.
    bot.unlocked_actions = ["move", "attack", "rest", "defend", "trap"]
    return bot


class TestSelfDictTrapFields:
    """state['me'] should expose trap info for the placing bot."""

    def test_traps_empty_by_default(self) -> None:
        bot = _bot()
        d = bot.to_self_dict()
        assert d["traps"] == []
        assert d["trap_cooldown"] == 0

    def test_traps_shows_own_traps(self) -> None:
        bot = _bot()
        tm = TrapManager()
        tm.place_trap("🤖", 5, 5, 30, round_num=1)
        tm.place_trap("🤖", 7, 7, 30, round_num=5)
        bot._trap_manager = tm
        bot._current_round = 8
        d = bot.to_self_dict()
        assert len(d["traps"]) == 2
        t0 = d["traps"][0]
        assert t0["x"] == 5
        assert t0["y"] == 5
        assert "expires_in" in t0

    def test_trap_cooldown_in_self_dict(self) -> None:
        bot = _bot()
        tm = TrapManager()
        tm.place_trap("🤖", 5, 5, 30, round_num=3)
        bot._trap_manager = tm
        bot._current_round = 4
        d = bot.to_self_dict()
        assert d["trap_cooldown"] == 2  # placed round 3, cooldown 3, so available at round 6

    def test_callbacks_in_self_dict(self) -> None:
        bot = _bot()
        bot.callbacks = CallbackSet(setup=lambda s: None, react=lambda s, e: None)
        d = bot.to_self_dict()
        assert "setup" in d["callbacks"]
        assert "react" in d["callbacks"]
        assert "on_kill" not in d["callbacks"]


class TestEnemyDictTrapFields:
    """state['enemies'][i] should show limited trap info."""

    def test_has_traps_false_by_default(self) -> None:
        bot = _bot()
        d = bot.to_enemy_dict()
        assert d["has_traps"] is False

    def test_has_traps_true_when_traps_exist(self) -> None:
        bot = _bot(emoji="🎯")
        tm = TrapManager()
        tm.place_trap("🎯", 5, 5, 30, round_num=1)
        bot._trap_manager = tm
        d = bot.to_enemy_dict()
        assert d["has_traps"] is True

    def test_enemy_trap_positions_not_exposed(self) -> None:
        bot = _bot(emoji="🎯")
        tm = TrapManager()
        tm.place_trap("🎯", 5, 5, 30, round_num=1)
        bot._trap_manager = tm
        d = bot.to_enemy_dict()
        assert "traps" not in d
        assert "trap_cooldown" not in d
