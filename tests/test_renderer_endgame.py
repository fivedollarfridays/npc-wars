"""Tests for renderer endgame: final frame and standings (T24.4)."""
from __future__ import annotations

import pytest


@pytest.fixture()
def players() -> list[dict]:
    return [
        {"emoji": "\U0001f480", "name": "Reaper"},   # skull
        {"emoji": "\U0001f916", "name": "RoboBot"},   # robot
        {"emoji": "\U0001f3af", "name": "KiteBot"},   # target
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


# -- render_final_frame ----------------------------------------------------

class TestRenderFinalFrame:
    """Final board state shown after match ends, before exiting alt screen."""

    def test_final_frame_contains_winner_emoji(self, players, round_data):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        output = renderer.render_final_frame(round_data, winner_emoji="\U0001f480")
        assert "\U0001f480" in output

    def test_final_frame_contains_winner_text(self, players, round_data):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        output = renderer.render_final_frame(round_data, winner_emoji="\U0001f480")
        assert "WINNER" in output

    def test_final_frame_does_not_exit_alt_screen(self, players, round_data):
        from agentgrounds.wars.cli.renderer import TerminalRenderer, _ALT_SCREEN_OFF

        renderer = TerminalRenderer(players=players, grid_size=10)
        output = renderer.render_final_frame(round_data, winner_emoji="\U0001f480")
        assert _ALT_SCREEN_OFF not in output


# -- render_standings ------------------------------------------------------

class TestRenderStandings:
    """Persistent standings table printed to normal scrollback."""

    @pytest.fixture()
    def match_data(self) -> dict:
        return {
            "winner": "\U0001f480",
            "duration_rounds": 38,
            "players": [
                {"emoji": "\U0001f480", "name": "Reaper"},
                {"emoji": "\U0001f916", "name": "RoboBot"},
                {"emoji": "\U0001f3af", "name": "KiteBot"},
            ],
            "stats": {
                "\U0001f480": {"kills": 2, "damage_dealt": 120, "damage_taken": 50, "rounds_survived": 38},
                "\U0001f916": {"kills": 1, "damage_dealt": 80, "damage_taken": 100, "rounds_survived": 35},
                "\U0001f3af": {"kills": 0, "damage_dealt": 40, "damage_taken": 90, "rounds_survived": 20},
            },
            "eliminations": [
                {"emoji": "\U0001f3af", "round": 20, "killed_by": "\U0001f480", "cause": "combat"},
                {"emoji": "\U0001f916", "round": 35, "killed_by": "storm", "cause": "storm"},
            ],
        }

    def test_standings_shows_placement_numbers(self, match_data):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(
            players=match_data["players"], grid_size=10,
        )
        output = renderer.render_standings(match_data)
        assert "1." in output
        assert "2." in output
        assert "3." in output

    def test_standings_shows_kills(self, match_data):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(
            players=match_data["players"], grid_size=10,
        )
        output = renderer.render_standings(match_data)
        assert "K:2" in output

    def test_standings_shows_elimination_round(self, match_data):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(
            players=match_data["players"], grid_size=10,
        )
        output = renderer.render_standings(match_data)
        assert "R20" in output or "R 20" in output

    def test_standings_winner_shows_survived(self, match_data):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(
            players=match_data["players"], grid_size=10,
        )
        output = renderer.render_standings(match_data)
        assert "38 rounds" in output

    def test_standings_title(self, match_data):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(
            players=match_data["players"], grid_size=10,
        )
        output = renderer.render_standings(match_data)
        assert "Final Standings" in output
