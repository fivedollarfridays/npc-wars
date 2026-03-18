"""Tests for combat overlay FX placement (extracted from test_renderer.py)."""
from __future__ import annotations

import pytest

from agentgrounds.wars.cli.overlay import build_combat_overlay
from agentgrounds.wars.cli.renderer import DEFEND_FX, WEAPON_FX


@pytest.fixture()
def players() -> list[dict]:
    return [
        {"emoji": "\U0001f480", "name": "Reaper"},
        {"emoji": "\U0001f916", "name": "RoboBot"},
        {"emoji": "\U0001f3af", "name": "KiteBot"},
    ]


class TestCombatOverlay:
    """Test build_combat_overlay produces correct FX placements."""

    def test_melee_hit_places_fx_on_attacker_cell_when_adjacent(self, players):
        """When attacker is adjacent to target, FX goes on attacker's cell."""
        positions = [
            {"emoji": "\U0001f480", "x": 3, "y": 5, "hp": 80, "energy": 60, "action": "attack", "alive": True},
            {"emoji": "\U0001f916", "x": 3, "y": 4, "hp": 45, "energy": 20, "action": "rest", "alive": True},
        ]
        events = [{"type": "hit", "attacker": "\U0001f480", "target": "\U0001f916", "damage": 25}]
        overlay = build_combat_overlay(positions, events)
        assert (3, 5) in overlay
        assert overlay[(3, 5)] == WEAPON_FX["melee"]

    def test_ranged_hit_places_fx_at_midpoint(self, players):
        """For ranged attacks, FX goes at the midpoint between attacker and target."""
        positions = [
            {"emoji": "\U0001f480", "x": 2, "y": 2, "hp": 80, "energy": 60, "action": "attack", "alive": True},
            {"emoji": "\U0001f916", "x": 6, "y": 2, "hp": 45, "energy": 20, "action": "rest", "alive": True},
        ]
        events = [{"type": "ranged_hit", "attacker": "\U0001f480", "target": "\U0001f916", "damage": 10}]
        overlay = build_combat_overlay(positions, events)
        assert (4, 2) in overlay
        assert overlay[(4, 2)] == WEAPON_FX["ranged"]

    def test_defend_event_places_shield_on_defender(self, players):
        """Defend event places shield FX on the defender's cell."""
        positions = [
            {"emoji": "\U0001f480", "x": 3, "y": 5, "hp": 80, "energy": 60, "action": "attack", "alive": True},
            {"emoji": "\U0001f916", "x": 5, "y": 5, "hp": 45, "energy": 20, "action": "defend", "alive": True},
        ]
        events = [{"type": "defend", "emoji": "\U0001f916"}]
        overlay = build_combat_overlay(positions, events)
        assert (5, 5) in overlay
        assert overlay[(5, 5)] == DEFEND_FX

    def test_miss_places_miss_fx_on_attacker(self, players):
        """Miss places miss FX on attacker's cell (no valid target hit)."""
        positions = [
            {"emoji": "\U0001f480", "x": 3, "y": 5, "hp": 80, "energy": 60, "action": "attack", "alive": True},
            {"emoji": "\U0001f916", "x": 3, "y": 2, "hp": 45, "energy": 20, "action": "rest", "alive": True},
        ]
        events = [{"type": "miss", "attacker": "\U0001f480", "direction": "north"}]
        overlay = build_combat_overlay(positions, events)
        assert (3, 5) in overlay
        assert overlay[(3, 5)] == WEAPON_FX["miss"]

    def test_kill_hit_uses_kill_fx(self, players):
        """When a hit target also appears as a kill victim, use kill FX."""
        positions = [
            {"emoji": "\U0001f480", "x": 3, "y": 5, "hp": 80, "energy": 60, "action": "attack", "alive": True},
            {"emoji": "\U0001f916", "x": 3, "y": 4, "hp": 5, "energy": 20, "action": "rest", "alive": True},
        ]
        events = [
            {"type": "hit", "attacker": "\U0001f480", "target": "\U0001f916", "damage": 25},
            {"type": "kill", "attacker": "\U0001f480", "victim": "\U0001f916"},
        ]
        overlay = build_combat_overlay(positions, events)
        assert (3, 5) in overlay
        assert overlay[(3, 5)] == WEAPON_FX["kill"]

    def test_defend_block_when_also_hit(self, players):
        """When a defending bot is also hit, use defend_block FX."""
        positions = [
            {"emoji": "\U0001f480", "x": 3, "y": 5, "hp": 80, "energy": 60, "action": "attack", "alive": True},
            {"emoji": "\U0001f916", "x": 5, "y": 5, "hp": 45, "energy": 20, "action": "defend", "alive": True},
        ]
        events = [
            {"type": "hit", "attacker": "\U0001f480", "target": "\U0001f916", "damage": 15},
            {"type": "defend", "emoji": "\U0001f916"},
        ]
        overlay = build_combat_overlay(positions, events)
        assert (5, 5) in overlay
        assert overlay[(5, 5)] == WEAPON_FX["defend_block"]

    def test_no_events_returns_empty_overlay(self, players):
        overlay = build_combat_overlay([], [])
        assert overlay == {}
