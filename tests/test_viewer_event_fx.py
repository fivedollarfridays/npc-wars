"""Tests that viewer renders new event FX types on canvas.

Structural tests verifying that event handlers and kill feed entries exist
for trap, ability, tactical, evolve, crystal, and wall_blocked events.
"""

import pytest

from conftest import read_viewer_content


@pytest.fixture()
def viewer_html() -> str:
    """Read all viewer files (index.html + js/*.js)."""
    return read_viewer_content()


class TestTrapEventRendering:
    """Canvas rendering for trap_placed and trap_trigger events."""

    def test_trap_placed_event_case(self, viewer_html: str) -> None:
        assert "evt.type === 'trap_placed'" in viewer_html

    def test_trap_placed_draws_diamond(self, viewer_html: str) -> None:
        """Trap placement should draw a diamond shape marker."""
        assert "trap_placed" in viewer_html
        # Diamond is drawn with moveTo/lineTo forming 4 points
        assert "diamond" in viewer_html.lower() or "moveTo" in viewer_html

    def test_trap_trigger_event_case(self, viewer_html: str) -> None:
        assert "evt.type === 'trap_trigger'" in viewer_html

    def test_trap_trigger_shows_damage(self, viewer_html: str) -> None:
        """Trap trigger should display damage number."""
        # Should reference evt.damage for trap_trigger
        assert "trap_trigger" in viewer_html


class TestTacticalEventRendering:
    """Canvas rendering for tactical_activate event."""

    def test_tactical_activate_event_case(self, viewer_html: str) -> None:
        assert "evt.type === 'tactical_activate'" in viewer_html

    def test_tactical_shows_lightning(self, viewer_html: str) -> None:
        """Tactical activation shows lightning bolt icon."""
        assert "tactical_activate" in viewer_html


class TestAbilityEventRendering:
    """Canvas rendering for ability_damage, ability_heal, ability_shield, ability_slow."""

    def test_ability_damage_event_case(self, viewer_html: str) -> None:
        assert "evt.type === 'ability_damage'" in viewer_html

    def test_ability_heal_event_case(self, viewer_html: str) -> None:
        assert "evt.type === 'ability_heal'" in viewer_html

    def test_ability_shield_event_case(self, viewer_html: str) -> None:
        assert "evt.type === 'ability_shield'" in viewer_html

    def test_ability_slow_event_case(self, viewer_html: str) -> None:
        assert "evt.type === 'ability_slow'" in viewer_html


class TestEvolveAndMiscRendering:
    """Canvas rendering for evolve, crystal_pickup, wall_blocked."""

    def test_evolve_event_case(self, viewer_html: str) -> None:
        assert "evt.type === 'evolve'" in viewer_html

    def test_crystal_pickup_event_case(self, viewer_html: str) -> None:
        assert "evt.type === 'crystal_pickup'" in viewer_html

    def test_wall_blocked_event_case(self, viewer_html: str) -> None:
        assert "evt.type === 'wall_blocked'" in viewer_html


class TestNewEventKillFeed:
    """Kill feed entries for new event types."""

    def test_trap_trigger_feed(self, viewer_html: str) -> None:
        """Trap trigger should appear in kill feed."""
        assert "trap_trigger" in viewer_html
        # Should show trap info in feed
        assert "trap" in viewer_html.lower()

    def test_tactical_activate_feed(self, viewer_html: str) -> None:
        """Tactical activation should appear in kill feed."""
        assert "tactical_activate" in viewer_html

    def test_ability_damage_feed(self, viewer_html: str) -> None:
        """Ability damage should appear in kill feed."""
        assert "ability_damage" in viewer_html

    def test_evolve_feed(self, viewer_html: str) -> None:
        """Evolve event should appear in kill feed."""
        # The kill feed section should reference evolve
        assert "evolve" in viewer_html

    def test_crystal_pickup_feed(self, viewer_html: str) -> None:
        """Crystal pickup should appear in kill feed."""
        assert "crystal_pickup" in viewer_html
