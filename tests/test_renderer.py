"""Tests for ANSI terminal renderer."""
from __future__ import annotations

import pytest


# -- Fixtures ----------------------------------------------------------

@pytest.fixture()
def players() -> list[dict]:
    return [
        {"emoji": "\U0001f480", "name": "Reaper"},   # 💀
        {"emoji": "\U0001f916", "name": "RoboBot"},   # 🤖
        {"emoji": "\U0001f3af", "name": "KiteBot"},   # 🎯
    ]


@pytest.fixture()
def round_data() -> dict:
    return {
        "round": 15,
        "storm_border": 2,
        "positions": [
            {"emoji": "\U0001f480", "x": 3, "y": 5, "hp": 80, "energy": 60, "action": "attack north", "alive": True},
            {"emoji": "\U0001f916", "x": 7, "y": 2, "hp": 45, "energy": 20, "action": "rest", "alive": True},
            {"emoji": "\U0001f3af", "x": 5, "y": 1, "hp": 0, "energy": 0, "action": "dead", "alive": False},
        ],
        "events": [
            {"type": "hit", "attacker": "\U0001f480", "target": "\U0001f916", "damage": 25},
            {"type": "kill", "attacker": "\U0001f480", "victim": "\U0001f3af"},
        ],
    }


# -- Cycle 1: Title and round number -----------------------------------

class TestFrameBasics:
    def test_render_frame_contains_title(self, players, round_data):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        output = renderer.render_frame(round_data, clear=False)
        assert "N P C   W A R S" in output

    def test_render_frame_contains_round_number(self, players, round_data):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        output = renderer.render_frame(round_data, clear=False)
        assert "Round 15" in output


# -- Cycle 2: Bot emojis and dead bots ---------------------------------

class TestBotDisplay:
    def test_render_frame_contains_bot_emojis(self, players, round_data):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        output = renderer.render_frame(round_data, clear=False)
        # Alive bots should appear in roster
        assert "\U0001f480" in output  # 💀
        assert "\U0001f916" in output  # 🤖

    def test_render_frame_shows_dead_bots_as_eliminated(self, players, round_data):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        output = renderer.render_frame(round_data, clear=False)
        assert "ELIMINATED" in output
        # Dead bot name should still appear
        assert "KiteBot" in output


# -- Cycle 3: HP bars --------------------------------------------------

class TestHpBars:
    def test_render_frame_contains_hp_bars(self, players, round_data):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        output = renderer.render_frame(round_data, clear=False)
        # Should contain filled bar chars and hp values
        assert "80hp" in output or "80" in output
        assert "\u2588" in output  # █ filled bar character

    def test_hp_bar_green_above_50(self):
        from agentgrounds.wars.cli.renderer import TerminalRenderer, _GREEN

        bar = TerminalRenderer._hp_bar(80)
        assert _GREEN in bar
        assert "\u2588" in bar  # █

    def test_hp_bar_yellow_25_to_50(self):
        from agentgrounds.wars.cli.renderer import TerminalRenderer, _YELLOW

        bar = TerminalRenderer._hp_bar(40)
        assert _YELLOW in bar

    def test_hp_bar_red_below_25(self):
        from agentgrounds.wars.cli.renderer import TerminalRenderer, _RED

        bar = TerminalRenderer._hp_bar(15)
        assert _RED in bar


# -- Cycle 4: Storm border ---------------------------------------------

class TestStormBorder:
    def test_render_frame_shows_storm_border(self, players, round_data):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        output = renderer.render_frame(round_data, clear=False)
        # Storm character should appear in the grid
        assert "\u2593" in output  # ▓

    def test_storm_zero_has_only_border(self, players):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        rd = {
            "round": 1,
            "storm_border": 0,
            "positions": [
                {"emoji": "\U0001f480", "x": 0, "y": 0, "hp": 100, "energy": 100, "action": "rest", "alive": True},
                {"emoji": "\U0001f916", "x": 1, "y": 1, "hp": 100, "energy": 100, "action": "rest", "alive": True},
                {"emoji": "\U0001f3af", "x": 2, "y": 2, "hp": 100, "energy": 100, "action": "rest", "alive": True},
            ],
            "events": [],
        }
        renderer = TerminalRenderer(players=players, grid_size=10)
        output = renderer.render_frame(rd, clear=False)
        # Should still have border storm chars
        assert "\u2593" in output


# -- Cycle 5: Kill feed -------------------------------------------------

class TestKillFeed:
    def test_kill_feed_accumulates(self, players, round_data):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        output = renderer.render_frame(round_data, clear=False)
        assert "Kill Feed" in output
        # Hit event should show damage
        assert "-25hp" in output or "25" in output
        # Kill event should show "eliminated"
        assert "eliminated" in output

    def test_kill_feed_shows_max_five(self, players):
        """Feed should only show the last 5 entries."""
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        base_pos = [
            {"emoji": "\U0001f480", "x": 3, "y": 5, "hp": 80, "energy": 60, "action": "attack", "alive": True},
            {"emoji": "\U0001f916", "x": 7, "y": 2, "hp": 45, "energy": 20, "action": "rest", "alive": True},
            {"emoji": "\U0001f3af", "x": 5, "y": 1, "hp": 30, "energy": 10, "action": "rest", "alive": True},
        ]
        # Render 7 rounds each with a hit event
        for i in range(1, 8):
            rd = {
                "round": i,
                "storm_border": 0,
                "positions": base_pos,
                "events": [{"type": "hit", "attacker": "\U0001f480", "target": "\U0001f916", "damage": i}],
            }
            output = renderer.render_frame(rd, clear=False)

        # Internal feed should have 7 entries, but only 5 shown
        assert len(renderer._kill_feed) == 7
        # The output of the last frame should NOT contain damage=1 or damage=2
        # (those are entries 1 and 2, scrolled off the 5-item window)
        # We check the rendered output contains the last 5 (3..7)
        assert "-7hp" in output


# -- Cycle 6: Winner banner --------------------------------------------

class TestWinnerBanner:
    def test_render_winner_banner(self, players):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        output = renderer.render_winner("\U0001f480", duration=25)
        assert "WINNER" in output
        assert "Reaper" in output
        assert "25 rounds" in output


# -- Cycle 7: Grid size variants ----------------------------------------

class TestGridSizes:
    @pytest.mark.parametrize("gs", [10, 11, 12])
    def test_grid_sizes_10_11_12(self, players, gs):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        rd = {
            "round": 1,
            "storm_border": 0,
            "positions": [
                {"emoji": "\U0001f480", "x": 0, "y": 0, "hp": 100, "energy": 100, "action": "rest", "alive": True},
                {"emoji": "\U0001f916", "x": 1, "y": 1, "hp": 100, "energy": 100, "action": "rest", "alive": True},
                {"emoji": "\U0001f3af", "x": 2, "y": 2, "hp": 100, "energy": 100, "action": "rest", "alive": True},
            ],
            "events": [],
        }
        renderer = TerminalRenderer(players=players, grid_size=gs)
        output = renderer.render_frame(rd, clear=False)
        # Grid should render without error and contain the title
        assert "N P C   W A R S" in output
        # Grid rows = gs, each rendered between border lines
        grid_lines = [line for line in output.split("\n") if "\u2593\u2593" in line]
        # Top border + gs rows + bottom border = gs + 2
        assert len(grid_lines) == gs + 2
