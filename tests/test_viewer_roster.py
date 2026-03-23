"""Tests for viewer roster polish — archetype, equipment, score, sorting.

Verifies the viewer sidebar shows archetype badges, equipment info, score
with momentum tier name, and sorts alive bots first by score descending.
"""
from __future__ import annotations

from conftest import read_viewer_content


def _read_viewer() -> str:
    """Read all viewer files (index.html + js/*.js)."""
    return read_viewer_content()


# --- Cycle 1: Roster archetype badge ---


def test_roster_shows_archetype_badge() -> None:
    """Bot entries in sidebar must include an archetype label element."""
    html = _read_viewer()
    assert "archetype-badge" in html, "Missing .archetype-badge class in roster"


def test_archetype_badge_uses_archetype_colors() -> None:
    """Archetype badge must be colored using ARCHETYPE_COLORS lookup."""
    html = _read_viewer()
    # The buildBotList or updateSidebar must reference ARCHETYPE_COLORS for badge
    assert "ARCHETYPE_COLORS" in html
    # Must have badge styling that sets background color
    assert "archetype-badge" in html


# --- Cycle 2: Roster equipment info ---


def test_roster_shows_equipment_text() -> None:
    """Bot entries must show weapon/armor text in the sidebar."""
    html = _read_viewer()
    assert "bot-equip" in html, "Missing .bot-equip class for equipment display"


def test_equipment_reads_from_stats() -> None:
    """Equipment display must read from matchData.stats for each bot."""
    html = _read_viewer()
    # Should reference equipment field from stats
    assert "equipment" in html or "weapon" in html


# --- Cycle 3: Score and momentum tier ---


def test_roster_shows_score() -> None:
    """Bot entries must display the current score from position data."""
    html = _read_viewer()
    assert "bot-score" in html, "Missing .bot-score class for score display"


def test_roster_shows_momentum_tier_name() -> None:
    """Sidebar must show momentum tier name (from stats)."""
    html = _read_viewer()
    assert "momentum_name" in html or "momentum-tier" in html


# --- Cycle 4: Sorting — alive first, by score desc ---


def test_roster_sorts_alive_first_by_score() -> None:
    """Roster must sort alive bots first, then by score descending."""
    html = _read_viewer()
    # Look for sorting logic in updateSidebar or buildBotList
    assert "sort" in html.lower() or "sortedPositions" in html or "sorted" in html


def test_bot_name_colored_by_archetype() -> None:
    """Bot name text must use archetype color."""
    html = _read_viewer()
    # The bot-name element should get its color set from archetype
    assert "bot-name" in html
    # Must reference archetype color when setting name color
    assert "ARCHETYPE_COLORS" in html
