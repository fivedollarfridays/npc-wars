"""Tests that viewer/match.html contains bump event rendering code.

These are structural tests that parse the HTML file and verify the expected
CSS animations, JS event handlers, and kill feed entries are present.
"""

from pathlib import Path

import pytest

VIEWER_PATH = Path(__file__).parent.parent / "viewer" / "match.html"


@pytest.fixture()
def viewer_html() -> str:
    """Read the viewer HTML file."""
    return VIEWER_PATH.read_text(encoding="utf-8")


class TestBumpCSSAnimations:
    """CSS keyframe animations for bump effects."""

    def test_wall_splat_keyframes(self, viewer_html: str) -> None:
        assert "@keyframes wallSplat" in viewer_html

    def test_storm_bounce_keyframes(self, viewer_html: str) -> None:
        assert "@keyframes stormBounce" in viewer_html

    def test_bump_arrow_keyframes(self, viewer_html: str) -> None:
        assert "@keyframes bumpArrow" in viewer_html


class TestBumpEventRendering:
    """JS handles bump/wall_splat/storm_bounce events on canvas."""

    def test_bump_event_case(self, viewer_html: str) -> None:
        assert "evt.type === 'bump'" in viewer_html

    def test_wall_splat_event_case(self, viewer_html: str) -> None:
        assert "evt.type === 'wall_splat'" in viewer_html

    def test_storm_bounce_event_case(self, viewer_html: str) -> None:
        assert "evt.type === 'storm_bounce'" in viewer_html

    def test_direction_arrow_mapping(self, viewer_html: str) -> None:
        """Direction string parsed to arrow character."""
        # Should map (1,0) -> arrow, etc.
        for arrow in ["→", "←", "↑", "↓"]:
            assert arrow in viewer_html, f"Missing arrow {arrow}"


class TestBumpKillFeed:
    """Kill feed shows bump event descriptions."""

    def test_bump_feed_entry(self, viewer_html: str) -> None:
        assert "bumped" in viewer_html

    def test_wall_splat_feed_entry(self, viewer_html: str) -> None:
        assert "wall splat" in viewer_html

    def test_storm_bounce_feed_entry(self, viewer_html: str) -> None:
        assert "storm" in viewer_html.lower() and "bounce" in viewer_html.lower()
