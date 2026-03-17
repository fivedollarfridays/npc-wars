"""Tests for attack swoosh and death explosion effects in viewer/match.html."""

from pathlib import Path

VIEWER_HTML = Path(__file__).resolve().parent.parent / "viewer" / "match.html"


def _read_html() -> str:
    return VIEWER_HTML.read_text()


def _function_chunk(html: str, func_name: str, size: int = 2500) -> str:
    """Extract a chunk of JS starting from a function definition."""
    start = html.index(f"function {func_name}(")
    return html[start : start + size]


class TestAttackSwooshFunction:
    """Verify attackSwoosh JS function exists and is animated."""

    def test_attack_swoosh_function_defined(self) -> None:
        html = _read_html()
        assert "function attackSwoosh(" in html

    def test_swoosh_uses_request_animation_frame(self) -> None:
        html = _read_html()
        chunk = _function_chunk(html, "attackSwoosh")
        assert "requestAnimationFrame" in chunk

    def test_swoosh_creates_overlay_canvas(self) -> None:
        html = _read_html()
        chunk = _function_chunk(html, "attackSwoosh")
        assert "createElement('canvas')" in chunk

    def test_swoosh_draws_arc(self) -> None:
        html = _read_html()
        chunk = _function_chunk(html, "attackSwoosh")
        assert ".arc(" in chunk

    def test_swoosh_removes_overlay_on_complete(self) -> None:
        html = _read_html()
        chunk = _function_chunk(html, "attackSwoosh")
        assert ".remove()" in chunk


class TestDeathExplosionFunction:
    """Verify deathExplosion JS function exists and is animated."""

    def test_death_explosion_function_defined(self) -> None:
        html = _read_html()
        assert "function deathExplosion(" in html

    def test_explosion_uses_request_animation_frame(self) -> None:
        html = _read_html()
        chunk = _function_chunk(html, "deathExplosion")
        assert "requestAnimationFrame" in chunk

    def test_explosion_creates_overlay_canvas(self) -> None:
        html = _read_html()
        chunk = _function_chunk(html, "deathExplosion")
        assert "createElement('canvas')" in chunk

    def test_explosion_spawns_particles(self) -> None:
        html = _read_html()
        chunk = _function_chunk(html, "deathExplosion")
        assert "particles" in chunk

    def test_explosion_removes_overlay_on_complete(self) -> None:
        html = _read_html()
        chunk = _function_chunk(html, "deathExplosion")
        assert ".remove()" in chunk


class TestEventsWiring:
    """Verify hit events trigger swoosh and kill events trigger explosion."""

    def test_hit_events_trigger_swoosh(self) -> None:
        html = _read_html()
        events_start = html.index("// Draw hit and bump effects")
        events_chunk = html[events_start : events_start + 3000]
        assert "attackSwoosh" in events_chunk

    def test_kill_events_trigger_explosion(self) -> None:
        html = _read_html()
        events_start = html.index("// Draw hit and bump effects")
        events_chunk = html[events_start : events_start + 3000]
        assert "deathExplosion" in events_chunk

    def test_swoosh_uses_attacker_and_target_positions(self) -> None:
        html = _read_html()
        events_start = html.index("// Draw hit and bump effects")
        events_chunk = html[events_start : events_start + 3000]
        # Hit handling should look up attacker position for swoosh origin
        assert "evt.attacker" in events_chunk
