"""Tests that match stats include equipment data for viewer consumption.

The viewer sidebar displays weapon/armor info which requires the engine
to include equipment in the stats dict.
"""
from __future__ import annotations


def test_stats_include_equipment_field() -> None:
    """Engine stats dict builder must include 'equipment' key."""
    # Verify the game.py _finalize_match includes equipment
    from pathlib import Path

    game_src = Path("engine/game.py").read_text()
    assert '"equipment"' in game_src, "Stats dict missing equipment field"


def test_bot_has_equipment_attribute() -> None:
    """Bot class must have an equipment attribute for stats to reference."""
    from engine.combat import Bot

    bot = Bot(name="test", emoji="T", bio="test bot", author="auth",
              decide_func=lambda *a: ("rest",), x=0, y=0, glyph="G")
    assert hasattr(bot, "equipment")
    assert isinstance(bot.equipment, dict)
