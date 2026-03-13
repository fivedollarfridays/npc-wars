"""Tests for consider-item fixes 12-15."""

import importlib

from engine.combat import Bot
from engine.game import run_match
from tests.conftest import bot_config, always_rest


# --- Fix 12: GooseLoose storm center deadlock ---


class TestGooseLooseStormCenter:
    def test_at_center_during_storm_does_not_default_west(self):
        """When bot is at center and storm is active, dx/dy should remain
        aimed at target, not overwritten to 0 (which defaults to 'west')."""
        from bots.goose_loose import decide

        # Place bot exactly at center of a 10x10 grid (center=5)
        # with storm_border=1 so storm is active, but bot is near edge
        # (x < storm_border+1 = 2 is false for x=5, so storm pull won't trigger)
        # To trigger the bug, bot must be near edge AND at center simultaneously.
        # Use grid_size=10, storm_border=4, bot at (5,5) which IS near edge:
        # 5 < 4+1=5 is false, 5 >= 10-4-1=5 is true -> triggers dy override
        # center = 10//2 = 5, cy_pull = 5-5 = 0 -> dy becomes 0
        # Enemy is to the south at (5,7), so original dy=2
        # Bug: dy overwritten to 0, so abs(dx=0) >= abs(dy=0) -> "west"
        state = {
            "me": {"x": 5, "y": 5, "hp": 100, "energy": 100,
                   "attack_power": 15, "defense": 0},
            "enemies": [{"name": "Target", "emoji": "T", "x": 5, "y": 7, "hp": 50}],
            "round": 30,
            "grid_size": 10,
            "storm_border": 4,
        }
        action = decide(state)
        # With the fix, dy should NOT be overwritten to 0, so bot moves south
        assert action == ("move", "south")

    def test_near_edge_with_nonzero_pull_still_overrides(self):
        """When bot is near edge and pull is non-zero, dx/dy should still be overridden."""
        from bots.goose_loose import decide

        # grid_size=10, storm_border=3, bot at (2,5)
        # x < 3+1=4 is true, center=5, cx_pull=5-2=3 (non-zero) -> dx=3
        # Enemy at (0,5), original dx=-2, dist=2 (not adjacent, won't attack)
        # With fix, cx_pull=3 != 0, so dx overridden to 3 -> moves east (toward center)
        state = {
            "me": {"x": 2, "y": 5, "hp": 100, "energy": 100,
                   "attack_power": 15, "defense": 0},
            "enemies": [{"name": "Target", "emoji": "T", "x": 0, "y": 5, "hp": 50}],
            "round": 30,
            "grid_size": 10,
            "storm_border": 3,
        }
        action = decide(state)
        assert action == ("move", "east")


# --- Fix 13: Bot.__init__ keyword-only args ---


class TestBotKeywordOnly:
    def test_keyword_args_work(self):
        """Bot can be created with all keyword arguments."""
        bot = Bot(name="Test", emoji="T", bio="b", author="a",
                  decide_func=lambda s: ("rest",), x=0, y=0)
        assert bot.name == "Test"

    def test_positional_args_rejected(self):
        """Bot cannot be created with positional arguments."""
        import pytest
        with pytest.raises(TypeError):
            Bot("Test", "T", "b", "a", lambda s: ("rest",), 0, 0)


# --- Fix 14: Single-bot run_match ---
# (Added directly to test_game.py per spec, but we test here too for TDD red phase)


class TestSingleBotMatch:
    def test_single_bot_match(self):
        """Single bot match ends immediately with that bot as winner."""
        configs = [
            bot_config("Solo", "\U0001f3af", always_rest),
        ]
        data = run_match(configs, seed=42)
        assert data["winner"] == "\U0001f3af"
        assert data["duration_rounds"] <= 1


# --- Fix 15: __all__ exports ---


class TestModuleAllExports:
    def test_combat_all(self):
        import engine.combat
        assert hasattr(engine.combat, "__all__")
        assert "Bot" in engine.combat.__all__
        assert "calculate_damage" in engine.combat.__all__
        assert "resolve_deaths" in engine.combat.__all__

    def test_grid_all(self):
        import engine.grid
        assert hasattr(engine.grid, "__all__")
        assert "calculate_grid_size" in engine.grid.__all__
        assert "DIRECTIONS" in engine.grid.__all__

    def test_sandbox_all(self):
        import engine.sandbox
        assert hasattr(engine.sandbox, "__all__")
        assert "execute_decide" in engine.sandbox.__all__
        assert "validate_action" in engine.sandbox.__all__

    def test_state_all(self):
        import engine.state
        assert hasattr(engine.state, "__all__")
        assert "build_state" in engine.state.__all__

    def test_match_writer_all(self):
        import engine.match_writer
        assert hasattr(engine.match_writer, "__all__")
        assert "write_match" in engine.match_writer.__all__

    def test_rounds_all(self):
        import engine.rounds
        assert hasattr(engine.rounds, "__all__")
        assert "resolve_decisions" in engine.rounds.__all__
        assert "build_round_record" in engine.rounds.__all__

    def test_game_all(self):
        import engine.game
        assert hasattr(engine.game, "__all__")
        assert "run_match" in engine.game.__all__
        assert "MAX_ROUNDS" in engine.game.__all__
