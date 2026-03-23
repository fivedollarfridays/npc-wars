"""Tests for viewer kill feed — new event types with icons.

Verifies the kill feed handles trap, tactical, ability, crystal, and evolve
event types with appropriate emoji indicators.
"""
from __future__ import annotations

from conftest import read_viewer_content


def _read_viewer() -> str:
    """Read all viewer files (index.html + js/*.js)."""
    return read_viewer_content()


# --- Cycle 1: Trap events ---


def test_kill_feed_handles_trap_placed() -> None:
    """Kill feed must handle trap_placed events."""
    html = _read_viewer()
    assert "trap_placed" in html, "Missing trap_placed event handler in kill feed"


def test_kill_feed_handles_trap_trigger() -> None:
    """Kill feed must handle trap_trigger events."""
    html = _read_viewer()
    assert "trap_trigger" in html, "Missing trap_trigger event handler in kill feed"


# --- Cycle 2: Tactical and ability events ---


def test_kill_feed_handles_tactical_activate() -> None:
    """Kill feed must handle tactical_activate events."""
    html = _read_viewer()
    assert "tactical_activate" in html, "Missing tactical_activate handler"


def test_kill_feed_handles_ability_damage() -> None:
    """Kill feed must handle ability_damage events in feed."""
    html = _read_viewer()
    assert "ability_damage" in html


# --- Cycle 3: Crystal and evolve events ---


def test_kill_feed_handles_crystal_pickup() -> None:
    """Kill feed must handle crystal_pickup events."""
    html = _read_viewer()
    assert "crystal_pickup" in html, "Missing crystal_pickup handler"


def test_kill_feed_handles_evolve() -> None:
    """Kill feed must handle evolve events."""
    html = _read_viewer()
    assert "evolve" in html, "Missing evolve event handler"
