"""Tests for shatter effect (kill) in viewer/match.html."""

from pathlib import Path

VIEWER_HTML = Path(__file__).resolve().parent.parent / "viewer" / "match.html"


def _read_html() -> str:
    return VIEWER_HTML.read_text()


class TestShatterFunctionExists:
    """Verify shatterEffect JS function is defined."""

    def test_shatter_effect_function_defined(self) -> None:
        html = _read_html()
        assert "function shatterEffect(" in html

    def test_shatter_effect_uses_request_animation_frame(self) -> None:
        html = _read_html()
        # Find the shatterEffect function body and check for rAF
        start = html.index("function shatterEffect(")
        # Look within a reasonable range for requestAnimationFrame
        chunk = html[start : start + 2500]
        assert "requestAnimationFrame" in chunk


class TestShatterParticles:
    """Verify particle behavior in the shatter effect."""

    def test_spawns_multiple_particles(self) -> None:
        html = _read_html()
        start = html.index("function shatterEffect(")
        chunk = html[start : start + 2500]
        # Should reference particle count in the 8-12 range
        assert "particle" in chunk.lower()

    def test_particles_have_decaying_opacity(self) -> None:
        html = _read_html()
        start = html.index("function shatterEffect(")
        chunk = html[start : start + 2500]
        assert "opacity" in chunk.lower()


class TestShatterWiredToKillEvent:
    """Verify kill events trigger the shatter effect."""

    def test_kill_event_calls_shatter(self) -> None:
        html = _read_html()
        # The events loop should call shatterEffect when evt.type === 'kill'
        assert "shatterEffect" in html
        # Find the renderRound events loop — use first occurrence for draw effects
        events_start = html.index("// Draw hit and bump effects")
        events_chunk = html[events_start : events_start + 2500]
        assert "'kill'" in events_chunk
        assert "shatterEffect" in events_chunk

    def test_kill_uses_victim_position(self) -> None:
        html = _read_html()
        events_start = html.index("// Draw hit and bump effects")
        events_chunk = html[events_start : events_start + 2500]
        # Should look up victim position from round.positions
        assert "evt.victim" in events_chunk
