"""Tests for progression fields in state dict (T9.9)."""

from engine.state import build_state
from engine.types import SelfInfo
from tests.conftest import make_bot


class TestUnlockedActions:
    """state['me']['unlocked_actions'] reflects bot's unlocked actions."""

    def test_unlocked_actions_in_self_dict(self):
        bot = make_bot(unlocked_actions=["move", "attack", "rest", "defend", "dash"])
        state = build_state(bot, [bot], round_num=1, grid_size=10, storm_border=0)
        assert state["me"]["unlocked_actions"] == ["move", "attack", "rest", "defend", "dash"]

    def test_unlocked_actions_is_list_of_strings(self):
        bot = make_bot(unlocked_actions=["move", "attack", "rest", "defend"])
        state = build_state(bot, [bot], round_num=1, grid_size=10, storm_border=0)
        assert isinstance(state["me"]["unlocked_actions"], list)
        assert all(isinstance(a, str) for a in state["me"]["unlocked_actions"])

    def test_unlocked_actions_is_copy(self):
        """Modifying the state dict should not change the bot's list."""
        bot = make_bot(unlocked_actions=["move", "attack", "rest", "defend"])
        state = build_state(bot, [bot], round_num=1, grid_size=10, storm_border=0)
        state["me"]["unlocked_actions"].append("ranged_attack")
        assert "ranged_attack" not in bot.unlocked_actions


class TestLineBudget:
    """state['me']['line_budget'] reflects bot's line budget."""

    def test_line_budget_in_self_dict(self):
        bot = make_bot(line_budget=120)
        state = build_state(bot, [bot], round_num=1, grid_size=10, storm_border=0)
        assert state["me"]["line_budget"] == 120

    def test_line_budget_is_int(self):
        bot = make_bot(line_budget=75)
        state = build_state(bot, [bot], round_num=1, grid_size=10, storm_border=0)
        assert isinstance(state["me"]["line_budget"], int)


class TestWinStreak:
    """state['me']['win_streak'] reflects bot's win streak."""

    def test_win_streak_in_self_dict(self):
        bot = make_bot(win_streak=5)
        state = build_state(bot, [bot], round_num=1, grid_size=10, storm_border=0)
        assert state["me"]["win_streak"] == 5

    def test_win_streak_is_int(self):
        bot = make_bot(win_streak=3)
        state = build_state(bot, [bot], round_num=1, grid_size=10, storm_border=0)
        assert isinstance(state["me"]["win_streak"], int)


class TestProgressionDefaults:
    """Default values when no progression data is set on bot."""

    def test_default_unlocked_actions(self):
        bot = make_bot()
        state = build_state(bot, [bot], round_num=1, grid_size=10, storm_border=0)
        assert sorted(state["me"]["unlocked_actions"]) == sorted(
            ["move", "attack", "rest", "defend"]
        )

    def test_default_line_budget(self):
        bot = make_bot()
        state = build_state(bot, [bot], round_num=1, grid_size=10, storm_border=0)
        assert state["me"]["line_budget"] == 50

    def test_default_win_streak(self):
        bot = make_bot()
        state = build_state(bot, [bot], round_num=1, grid_size=10, storm_border=0)
        assert state["me"]["win_streak"] == 0


class TestSelfInfoTypedDict:
    """SelfInfo TypedDict includes progression fields."""

    def test_unlocked_actions_key_in_selfinfo(self):
        assert "unlocked_actions" in SelfInfo.__annotations__

    def test_line_budget_key_in_selfinfo(self):
        assert "line_budget" in SelfInfo.__annotations__

    def test_win_streak_key_in_selfinfo(self):
        assert "win_streak" in SelfInfo.__annotations__
