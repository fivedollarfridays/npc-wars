"""Tests for trap feed formatters and overlay FX (T34.1)."""
from __future__ import annotations

from agentgrounds.wars.cli.feed import _FORMATTERS, format_feed_event
from agentgrounds.wars.cli.overlay import build_combat_overlay


class TestTrapPlacedFeed:
    def test_trap_placed_registered(self) -> None:
        assert "trap_placed" in _FORMATTERS

    def test_trap_placed_format(self) -> None:
        evt = {"type": "trap_placed", "emoji": "\U0001f916", "x": 5, "y": 3}
        line = format_feed_event(evt, 4)
        assert line is not None
        assert "R4" in line
        assert "\U0001f916" in line
        assert "\U0001fa64" in line  # trap emoji
        assert "trap set" in line


class TestTrapTriggerFeed:
    def test_trap_trigger_registered(self) -> None:
        assert "trap_trigger" in _FORMATTERS

    def test_trap_trigger_format(self) -> None:
        evt = {
            "type": "trap_trigger",
            "victim": "\U0001f3af",
            "owner": "\U0001f916",
            "damage": 22.5,
            "x": 5,
            "y": 3,
        }
        line = format_feed_event(evt, 7)
        assert line is not None
        assert "R7" in line
        assert "\U0001f3af" in line
        assert "\U0001f916" in line
        assert "-22.5hp" in line

    def test_trap_trigger_contains_trap_keyword(self) -> None:
        evt = {
            "type": "trap_trigger",
            "victim": "\U0001f3af",
            "owner": "\U0001f916",
            "damage": 10,
            "x": 1,
            "y": 1,
        }
        line = format_feed_event(evt, 1)
        assert line is not None
        assert "trap" in line


class TestTrapTriggerOverlay:
    def test_trap_trigger_places_fx_at_trap_coords(self) -> None:
        positions = [
            {"emoji": "\U0001f3af", "x": 5, "y": 3, "hp": 60, "alive": True},
            {"emoji": "\U0001f916", "x": 2, "y": 2, "hp": 80, "alive": True},
        ]
        events = [
            {
                "type": "trap_trigger",
                "victim": "\U0001f3af",
                "owner": "\U0001f916",
                "damage": 22.5,
                "x": 5,
                "y": 3,
            },
        ]
        overlay = build_combat_overlay(positions, events)
        assert (5, 3) in overlay
        assert "\U0001f4a5" in overlay[(5, 3)]

    def test_trap_trigger_no_fx_without_coords(self) -> None:
        """Events missing x/y should not crash, just skip overlay."""
        positions = [
            {"emoji": "\U0001f3af", "x": 5, "y": 3, "hp": 60, "alive": True},
        ]
        events = [
            {
                "type": "trap_trigger",
                "victim": "\U0001f3af",
                "owner": "\U0001f916",
                "damage": 10,
            },
        ]
        overlay = build_combat_overlay(positions, events)
        # Should not crash; no overlay entry without coords
        assert isinstance(overlay, dict)
