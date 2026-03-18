"""Tests for momentum display in roster, aura overlay, and standings (T25.4)."""
from __future__ import annotations

import pytest


# -- Fixtures ----------------------------------------------------------

@pytest.fixture()
def players() -> list[dict]:
    return [
        {"emoji": "\U0001f480", "name": "Reaper"},   # skull
        {"emoji": "\U0001f916", "name": "RoboBot"},   # robot
        {"emoji": "\U0001f3af", "name": "KiteBot"},   # target
    ]


def _pos(emoji: str, *, x: int = 3, y: int = 5, hp: int = 80,
         energy: int = 60, alive: bool = True, score: int = 0,
         momentum_tier: int = 0) -> dict:
    """Helper to build a position dict with momentum fields."""
    return {
        "emoji": emoji, "x": x, "y": y, "hp": hp, "energy": energy,
        "action": "rest", "alive": alive, "score": score,
        "momentum_tier": momentum_tier,
    }


# -- Cycle 1: Roster score display ------------------------------------

class TestRosterScore:
    def test_roster_shows_score_in_brackets(self, players):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        positions = [
            _pos("\U0001f480", score=12),
            _pos("\U0001f916", score=28),
            _pos("\U0001f3af", alive=False, hp=0, score=8),
        ]
        rd = {"round": 5, "storm_border": 0, "positions": positions, "events": []}
        output = renderer.render_frame(rd, clear=False)
        assert "[12 pts]" in output
        assert "[28 pts]" in output

    def test_roster_shows_score_for_eliminated_bots(self, players):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        positions = [
            _pos("\U0001f480", score=12),
            _pos("\U0001f916", score=28),
            _pos("\U0001f3af", alive=False, hp=0, score=8),
        ]
        rd = {"round": 5, "storm_border": 0, "positions": positions, "events": []}
        output = renderer.render_frame(rd, clear=False)
        assert "[8 pts]" in output


# -- Cycle 2: Roster tier labels ---------------------------------------

class TestRosterTierLabels:
    def test_no_tier_label_for_tier_0(self, players):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        positions = [
            _pos("\U0001f480", score=5, momentum_tier=0),
            _pos("\U0001f916", score=0, momentum_tier=0),
            _pos("\U0001f3af", score=0, momentum_tier=0),
        ]
        rd = {"round": 5, "storm_border": 0, "positions": positions, "events": []}
        output = renderer.render_frame(rd, clear=False)
        assert "MOMENTUM" not in output
        assert "BATTLE FURY" not in output
        assert "CROWD FAVORITE" not in output
        assert "UNSTOPPABLE" not in output

    def test_tier_1_shows_momentum(self, players):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        positions = [
            _pos("\U0001f480", score=15, momentum_tier=1),
            _pos("\U0001f916", score=0, momentum_tier=0),
            _pos("\U0001f3af", score=0, momentum_tier=0),
        ]
        rd = {"round": 5, "storm_border": 0, "positions": positions, "events": []}
        output = renderer.render_frame(rd, clear=False)
        assert "MOMENTUM" in output

    def test_tier_2_shows_battle_fury(self, players):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        positions = [
            _pos("\U0001f480", score=30, momentum_tier=2),
            _pos("\U0001f916", score=0, momentum_tier=0),
            _pos("\U0001f3af", score=0, momentum_tier=0),
        ]
        rd = {"round": 5, "storm_border": 0, "positions": positions, "events": []}
        output = renderer.render_frame(rd, clear=False)
        assert "BATTLE FURY" in output

    def test_tier_3_shows_crowd_favorite(self, players):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        positions = [
            _pos("\U0001f480", score=45, momentum_tier=3),
            _pos("\U0001f916", score=0, momentum_tier=0),
            _pos("\U0001f3af", score=0, momentum_tier=0),
        ]
        rd = {"round": 5, "storm_border": 0, "positions": positions, "events": []}
        output = renderer.render_frame(rd, clear=False)
        assert "CROWD FAVORITE" in output

    def test_tier_4_shows_unstoppable(self, players):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        renderer = TerminalRenderer(players=players, grid_size=10)
        positions = [
            _pos("\U0001f480", score=65, momentum_tier=4),
            _pos("\U0001f916", score=0, momentum_tier=0),
            _pos("\U0001f3af", score=0, momentum_tier=0),
        ]
        rd = {"round": 5, "storm_border": 0, "positions": positions, "events": []}
        output = renderer.render_frame(rd, clear=False)
        assert "UNSTOPPABLE" in output


# -- Cycle 3: Aura overlay --------------------------------------------

class TestAuraOverlay:
    def test_no_aura_for_tier_0(self):
        from agentgrounds.wars.cli.overlay import build_aura_overlay

        positions = [_pos("\U0001f480", x=5, y=5, momentum_tier=0)]
        result = build_aura_overlay(positions, grid_size=10, storm_border=0)
        assert result == {}

    def test_no_aura_for_tier_2(self):
        from agentgrounds.wars.cli.overlay import build_aura_overlay

        positions = [_pos("\U0001f480", x=5, y=5, momentum_tier=2)]
        result = build_aura_overlay(positions, grid_size=10, storm_border=0)
        assert result == {}

    def test_tier_3_aura_adjacent_cells(self):
        from agentgrounds.wars.cli.overlay import build_aura_overlay

        positions = [_pos("\U0001f480", x=5, y=5, momentum_tier=3)]
        result = build_aura_overlay(positions, grid_size=10, storm_border=0)
        # Should have up to 4 adjacent cells
        assert (4, 5) in result  # left
        assert (6, 5) in result  # right
        assert (5, 4) in result  # up
        assert (5, 6) in result  # down
        assert len(result) == 4

    def test_tier_4_aura_adjacent_cells(self):
        from agentgrounds.wars.cli.overlay import build_aura_overlay

        positions = [_pos("\U0001f480", x=5, y=5, momentum_tier=4)]
        result = build_aura_overlay(positions, grid_size=10, storm_border=0)
        assert len(result) == 4
        assert (4, 5) in result

    def test_aura_skips_occupied_cells(self):
        from agentgrounds.wars.cli.overlay import build_aura_overlay

        positions = [
            _pos("\U0001f480", x=5, y=5, momentum_tier=3),
            _pos("\U0001f916", x=6, y=5),  # occupies a neighbor
        ]
        result = build_aura_overlay(positions, grid_size=10, storm_border=0)
        assert (6, 5) not in result  # occupied by RoboBot
        assert (4, 5) in result
        assert (5, 4) in result
        assert (5, 6) in result

    def test_aura_skips_storm_cells(self):
        from agentgrounds.wars.cli.overlay import build_aura_overlay

        # Bot at edge, storm_border=1 means cells at x<1 are storm
        positions = [_pos("\U0001f480", x=1, y=5, momentum_tier=3)]
        result = build_aura_overlay(positions, grid_size=10, storm_border=1)
        assert (0, 5) not in result  # in storm

    def test_aura_skips_out_of_bounds(self):
        from agentgrounds.wars.cli.overlay import build_aura_overlay

        positions = [_pos("\U0001f480", x=0, y=0, momentum_tier=3)]
        result = build_aura_overlay(positions, grid_size=10, storm_border=0)
        assert (-1, 0) not in result
        assert (0, -1) not in result
        assert len(result) == 2  # only right and down

    def test_aura_dead_bot_no_aura(self):
        from agentgrounds.wars.cli.overlay import build_aura_overlay

        positions = [_pos("\U0001f480", x=5, y=5, momentum_tier=3, alive=False, hp=0)]
        result = build_aura_overlay(positions, grid_size=10, storm_border=0)
        assert result == {}


# -- Cycle 4: Standings score + tier -----------------------------------

class TestStandingsScore:
    def test_standings_shows_score(self, players):
        from agentgrounds.wars.cli.standings import build_standings

        match_data = {
            "winner": "\U0001f480",
            "duration_rounds": 38,
            "eliminations": [
                {"emoji": "\U0001f3af", "round": 20},
                {"emoji": "\U0001f916", "round": 35},
            ],
            "stats": {
                "\U0001f480": {"kills": 2, "damage_dealt": 120, "score": 68, "momentum_tier": 3},
                "\U0001f916": {"kills": 1, "damage_dealt": 80, "score": 30, "momentum_tier": 2},
                "\U0001f3af": {"kills": 0, "damage_dealt": 40, "score": 10, "momentum_tier": 1},
            },
        }
        player_names = {p["emoji"]: p["name"] for p in players}
        output = build_standings(match_data, player_names)
        assert "Score:68" in output or "Score: 68" in output

    def test_standings_shows_tier_name(self, players):
        from agentgrounds.wars.cli.standings import build_standings

        match_data = {
            "winner": "\U0001f480",
            "duration_rounds": 38,
            "eliminations": [
                {"emoji": "\U0001f3af", "round": 20},
                {"emoji": "\U0001f916", "round": 35},
            ],
            "stats": {
                "\U0001f480": {"kills": 2, "damage_dealt": 120, "score": 68, "momentum_tier": 3},
                "\U0001f916": {"kills": 1, "damage_dealt": 80, "score": 30, "momentum_tier": 2},
                "\U0001f3af": {"kills": 0, "damage_dealt": 40, "score": 10, "momentum_tier": 1},
            },
        }
        player_names = {p["emoji"]: p["name"] for p in players}
        output = build_standings(match_data, player_names)
        assert "CROWD FAVORITE" in output

    def test_standings_no_tier_for_tier_0(self, players):
        from agentgrounds.wars.cli.standings import build_standings

        match_data = {
            "winner": "\U0001f480",
            "duration_rounds": 10,
            "eliminations": [
                {"emoji": "\U0001f3af", "round": 5},
                {"emoji": "\U0001f916", "round": 8},
            ],
            "stats": {
                "\U0001f480": {"kills": 2, "damage_dealt": 50, "score": 5, "momentum_tier": 0},
                "\U0001f916": {"kills": 0, "damage_dealt": 20, "score": 3, "momentum_tier": 0},
                "\U0001f3af": {"kills": 0, "damage_dealt": 10, "score": 1, "momentum_tier": 0},
            },
        }
        player_names = {p["emoji"]: p["name"] for p in players}
        output = build_standings(match_data, player_names)
        assert "MOMENTUM" not in output
        assert "BATTLE FURY" not in output
        assert "CROWD FAVORITE" not in output
        assert "UNSTOPPABLE" not in output
