"""Tests for terrain event feed formatters."""
from __future__ import annotations

from agentgrounds.wars.cli.feed import format_feed_event


def test_wall_blocked_format() -> None:
    evt = {"type": "wall_blocked", "emoji": "\U0001f916", "x": 3, "y": 5}
    result = format_feed_event(evt, 4)
    assert result is not None
    assert "R4" in result
    assert "\U0001f916" in result
    assert "wall" in result.lower()


def test_crystal_pickup_format() -> None:
    evt = {"type": "crystal_pickup", "emoji": "\U0001f916", "x": 5, "y": 3, "energy": 10}
    result = format_feed_event(evt, 2)
    assert result is not None
    assert "R2" in result
    assert "\U0001f916" in result
    assert "10" in result
    assert "crystal" in result.lower() or "\u2728" in result


def test_terrain_blocked_format() -> None:
    evt = {"type": "terrain_blocked", "attacker": "\U0001f916", "target": "\U0001f3af", "reason": "wall"}
    result = format_feed_event(evt, 7)
    assert result is not None
    assert "R7" in result
    assert "\U0001f916" in result
    assert "wall" in result.lower() or "blocked" in result.lower()


def test_water_penalty_format() -> None:
    evt = {"type": "water_penalty", "emoji": "\U0001f916", "x": 2, "y": 8, "cost": 3}
    result = format_feed_event(evt, 3)
    assert result is not None
    assert "R3" in result
    assert "\U0001f916" in result
    assert "3" in result


def test_unknown_event_still_none() -> None:
    """Ensure unknown events still return None."""
    evt = {"type": "totally_unknown_event_xyz"}
    assert format_feed_event(evt, 1) is None
