"""Sprint 24 integration tests: kill feed expansion + animation pipeline."""
from __future__ import annotations

import pytest

from agentgrounds.wars.cli.renderer import (
    WEAPON_FX,
    TerminalRenderer,
)


# -- Fixtures --------------------------------------------------------------

@pytest.fixture()
def players() -> list[dict]:
    return [
        {"emoji": "\U0001f916", "name": "RoboBot"},
        {"emoji": "\U0001f3af", "name": "KiteBot"},
        {"emoji": "\U0001f9e0", "name": "BrainBot"},
        {"emoji": "\U0001f40e", "name": "TankBot"},
    ]


@pytest.fixture()
def renderer(players: list[dict]) -> TerminalRenderer:
    return TerminalRenderer(players=players, grid_size=10)


@pytest.fixture()
def base_positions() -> list[dict]:
    return [
        {"emoji": "\U0001f916", "x": 3, "y": 3, "hp": 80, "energy": 60, "action": "attack east", "alive": True},
        {"emoji": "\U0001f3af", "x": 5, "y": 5, "hp": 60, "energy": 40, "action": "rest", "alive": True},
        {"emoji": "\U0001f9e0", "x": 7, "y": 7, "hp": 50, "energy": 30, "action": "rest", "alive": True},
        {"emoji": "\U0001f40e", "x": 1, "y": 1, "hp": 100, "energy": 100, "action": "defend", "alive": True},
    ]


# -- Part 1: Kill feed expansion ------------------------------------------

class TestKillFeedMiss:
    def test_miss_event_in_feed(self, renderer: TerminalRenderer, base_positions: list[dict]) -> None:
        events = [{"type": "miss", "attacker": "\U0001f916", "direction": "east"}]
        rd = {"round": 5, "storm_border": 0, "positions": base_positions, "events": events}
        output = renderer.render_frame(rd, clear=False)
        assert "missed" in output
        assert "east" in output

    def test_ranged_miss_event_in_feed(self, renderer: TerminalRenderer, base_positions: list[dict]) -> None:
        events = [{"type": "ranged_miss", "attacker": "\U0001f916", "direction": "east"}]
        rd = {"round": 5, "storm_border": 0, "positions": base_positions, "events": events}
        output = renderer.render_frame(rd, clear=False)
        assert "missed" in output


class TestKillFeedDefend:
    def test_defend_event_in_feed(self, renderer: TerminalRenderer, base_positions: list[dict]) -> None:
        events = [{"type": "defend", "emoji": "\U0001f40e"}]
        rd = {"round": 5, "storm_border": 0, "positions": base_positions, "events": events}
        output = renderer.render_frame(rd, clear=False)
        assert "defending" in output


class TestKillFeedDash:
    def test_dash_event_in_feed(self, renderer: TerminalRenderer, base_positions: list[dict]) -> None:
        events = [{"type": "dash", "emoji": "\U0001f3af", "from_x": 5, "from_y": 5, "to_x": 5, "to_y": 3}]
        rd = {"round": 5, "storm_border": 0, "positions": base_positions, "events": events}
        output = renderer.render_frame(rd, clear=False)
        assert "dashed" in output


class TestKillFeedEnvironment:
    def test_wall_splat_event_in_feed(self, renderer: TerminalRenderer, base_positions: list[dict]) -> None:
        events = [{"type": "wall_splat", "target": "\U0001f3af", "damage": 10}]
        rd = {"round": 5, "storm_border": 0, "positions": base_positions, "events": events}
        output = renderer.render_frame(rd, clear=False)
        assert "wall splat" in output
        assert "-10hp" in output

    def test_storm_bounce_event_in_feed(self, renderer: TerminalRenderer, base_positions: list[dict]) -> None:
        events = [{"type": "storm_bounce", "target": "\U0001f3af", "damage": 10}]
        rd = {"round": 5, "storm_border": 0, "positions": base_positions, "events": events}
        output = renderer.render_frame(rd, clear=False)
        assert "storm bounce" in output
        assert "-10hp" in output


class TestKillFeedTaunt:
    def test_taunt_event_in_feed(self, renderer: TerminalRenderer, base_positions: list[dict]) -> None:
        events = [{"type": "taunt", "taunter": "\U0001f9e0", "affected": ["\U0001f916", "\U0001f3af"]}]
        rd = {"round": 5, "storm_border": 0, "positions": base_positions, "events": events}
        output = renderer.render_frame(rd, clear=False)
        assert "taunted" in output


# -- Part 2: Integration pipeline tests ------------------------------------

class TestDefendEventsInMatch:
    def test_defend_events_exist_in_real_match(self) -> None:
        """Run a real match with builtin bots; at least one defend event should exist."""
        from engine.game import run_match
        from engine.loader import load_bots

        bot_configs = load_bots("agentgrounds/wars/builtin_bots")
        match_data = run_match(bot_configs, match_id=999, seed=42)

        found_defend = False
        for rd in match_data.get("rounds", []):
            for evt in rd.get("events", []):
                if evt.get("type") == "defend":
                    found_defend = True
                    break
            if found_defend:
                break
        assert found_defend, "No defend events found in match with builtin bots"


class TestTankBotEmoji:
    def test_tankbot_is_turtle_in_match(self) -> None:
        """TankBot should appear as turtle emoji in match player list."""
        from engine.game import run_match
        from engine.loader import load_bots

        bot_configs = load_bots("agentgrounds/wars/builtin_bots")
        match_data = run_match(bot_configs, match_id=998, seed=42)

        players = match_data.get("players", [])
        tank_player = [p for p in players if p.get("name") == "TankBot"]
        assert len(tank_player) == 1, "TankBot not found in players"
        assert tank_player[0]["emoji"] == "\U0001f422", f"TankBot emoji is {tank_player[0]['emoji']!r}, expected turtle"


class TestRendererActionFrameFX:
    def test_action_frame_has_weapon_fx(self) -> None:
        """render_action_frame with a hit event should contain weapon FX."""
        players = [
            {"emoji": "\U0001f916", "name": "RoboBot"},
            {"emoji": "\U0001f3af", "name": "KiteBot"},
        ]
        renderer = TerminalRenderer(players=players, grid_size=10)
        rd = {
            "round": 3,
            "storm_border": 0,
            "positions": [
                {"emoji": "\U0001f916", "x": 3, "y": 3, "hp": 80, "energy": 60, "action": "attack", "alive": True},
                {"emoji": "\U0001f3af", "x": 3, "y": 4, "hp": 60, "energy": 40, "action": "rest", "alive": True},
            ],
            "events": [{"type": "hit", "attacker": "\U0001f916", "target": "\U0001f3af", "damage": 20}],
        }
        output = renderer.render_action_frame(rd, clear=False)
        assert WEAPON_FX["melee"] in output


class TestRendererFinalFrame:
    def test_final_frame_contains_winner(self) -> None:
        """render_final_frame output should contain WINNER."""
        players = [
            {"emoji": "\U0001f916", "name": "RoboBot"},
            {"emoji": "\U0001f3af", "name": "KiteBot"},
        ]
        renderer = TerminalRenderer(players=players, grid_size=10)
        rd = {
            "round": 20,
            "storm_border": 3,
            "positions": [
                {"emoji": "\U0001f916", "x": 5, "y": 5, "hp": 40, "energy": 30, "action": "rest", "alive": True},
                {"emoji": "\U0001f3af", "x": 0, "y": 0, "hp": 0, "energy": 0, "action": "dead", "alive": False},
            ],
        }
        output = renderer.render_final_frame(rd, "\U0001f916")
        assert "WINNER" in output


class TestRendererStandings:
    def test_standings_contains_placement_numbers(self) -> None:
        """render_standings should show numbered placements."""
        players = [
            {"emoji": "\U0001f916", "name": "RoboBot"},
            {"emoji": "\U0001f3af", "name": "KiteBot"},
        ]
        renderer = TerminalRenderer(players=players, grid_size=10)
        match_data = {
            "winner": "\U0001f916",
            "duration_rounds": 20,
            "eliminations": [{"emoji": "\U0001f3af", "round": 18}],
            "stats": {
                "\U0001f916": {"kills": 1, "damage_dealt": 80},
                "\U0001f3af": {"kills": 0, "damage_dealt": 30},
            },
        }
        output = renderer.render_standings(match_data)
        assert "1." in output
        assert "2." in output
        assert "Final Standings" in output


class TestWeaponFXDict:
    def test_weapon_fx_has_required_keys(self) -> None:
        assert "melee" in WEAPON_FX
        assert "ranged" in WEAPON_FX
        assert "default" in WEAPON_FX


class TestNoFxFlag:
    def test_play_parser_accepts_no_fx(self) -> None:
        """The play subcommand parser should accept --no-fx."""
        import argparse

        from agentgrounds.wars.cli.cmd_play import register

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        register(subparsers)
        args = parser.parse_args(["play", "--no-fx"])
        assert args.no_fx is True

    def test_watch_parser_accepts_no_fx(self) -> None:
        """The watch subcommand parser should accept --no-fx."""
        import argparse

        from agentgrounds.wars.cli.cmd_watch import register

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        register(subparsers)
        args = parser.parse_args(["watch", "test.json", "--no-fx"])
        assert args.no_fx is True
