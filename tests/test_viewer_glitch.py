"""Tests for T15.3: Spectacle glitch effect (storm_kill)."""

from conftest import read_viewer_content


def _read_html() -> str:
    return read_viewer_content()


def test_glitch_rgb_keyframes_exist():
    """CSS @keyframes glitch-rgb animation is defined."""
    html = _read_html()
    assert "@keyframes glitch-rgb" in html


def test_glitch_effect_css_class_exists():
    """.glitch-effect CSS class is defined."""
    html = _read_html()
    assert ".glitch-effect" in html


def test_glitch_scanlines_css_exists():
    """.glitch-scanlines pseudo-element rule is defined."""
    html = _read_html()
    assert ".glitch-scanlines" in html


def test_glitch_effect_function_exists():
    """glitchEffect JS function is defined."""
    html = _read_html()
    assert "function glitchEffect()" in html


def test_storm_kill_trigger_calls_glitch():
    """storm_kill trigger in applySpectacleEffects calls glitchEffect."""
    html = _read_html()
    assert "triggers.includes('storm_kill')" in html
    assert "glitchEffect()" in html


def test_glitch_effect_duration_400ms():
    """Glitch effect uses 0.4s duration."""
    html = _read_html()
    assert "0.4s" in html


def test_glitch_effect_cleanup():
    """Glitch effect removes classes after timeout."""
    html = _read_html()
    assert "classList.remove('glitch-effect'" in html


def test_glitch_rgb_has_red_blue_channels():
    """RGB offset uses red and blue color channels."""
    html = _read_html()
    assert "rgba(255,0,0" in html
    assert "rgba(0,0,255" in html
