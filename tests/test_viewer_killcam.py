"""Tests for kill cam + death animation in viewer."""

from pathlib import Path

from conftest import read_viewer_content

EFFECTS_PATH = Path(__file__).parent.parent / "viewer" / "js" / "effects.js"


def _read_html() -> str:
    return read_viewer_content()


def _read_effects() -> str:
    return EFFECTS_PATH.read_text(encoding="utf-8")


class TestKillCamFunctionExists:
    """Verify triggerKillCam JS function is defined in effects.js."""

    def test_trigger_kill_cam_defined(self) -> None:
        src = _read_effects()
        assert "function triggerKillCam(" in src

    def test_update_kill_cam_defined(self) -> None:
        src = _read_effects()
        assert "function updateKillCam(" in src

    def test_kill_cam_uses_css_transform(self) -> None:
        src = _read_effects()
        start = src.index("function triggerKillCam(")
        chunk = src[start : start + 1500]
        assert "scale(" in chunk


class TestDeathAnimationExists:
    """Verify playDeathAnimation JS function is defined."""

    def test_play_death_animation_defined(self) -> None:
        src = _read_effects()
        assert "function playDeathAnimation(" in src

    def test_death_animation_uses_raf(self) -> None:
        src = _read_effects()
        start = src.index("function playDeathAnimation(")
        chunk = src[start : start + 2000]
        assert "requestAnimationFrame" in chunk

    def test_death_animation_has_particle_burst(self) -> None:
        src = _read_effects()
        start = src.index("function playDeathAnimation(")
        chunk = src[start : start + 2000]
        assert "particle" in chunk.lower()


class TestKillCamWiredToEvents:
    """Verify kill events trigger kill cam in events.js."""

    def test_kill_event_calls_trigger_kill_cam(self) -> None:
        html = _read_html()
        events_start = html.index("function renderEventFX(")
        events_chunk = html[events_start : events_start + 6000]
        assert "triggerKillCam" in events_chunk

    def test_kill_event_calls_play_death_animation(self) -> None:
        html = _read_html()
        events_start = html.index("function renderEventFX(")
        events_chunk = html[events_start : events_start + 6000]
        assert "playDeathAnimation" in events_chunk


class TestKillCamSpeedControl:
    """Kill cam should slow down playback speed."""

    def test_kill_cam_slows_speed(self) -> None:
        src = _read_effects()
        start = src.index("function triggerKillCam(")
        chunk = src[start : start + 1500]
        # Should set speed to a fraction (slow-mo)
        assert "speed" in chunk

    def test_update_kill_cam_restores_speed(self) -> None:
        src = _read_effects()
        start = src.index("function updateKillCam(")
        chunk = src[start : start + 1500]
        assert "speed" in chunk


class TestEffectsFileSizeLimit:
    """Effects.js must stay under 600 lines (extended for round transitions)."""

    def test_effects_under_600_lines(self) -> None:
        src = _read_effects()
        line_count = src.count("\n") + 1
        assert line_count < 600, f"effects.js is {line_count} lines (limit 600)"
