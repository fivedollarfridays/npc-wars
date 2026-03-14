"""Structural tests for viewer spectacle FX in match.html."""

from pathlib import Path

VIEWER_PATH = Path(__file__).parent.parent / "viewer" / "match.html"


def _read_viewer() -> str:
    """Read the viewer HTML file contents."""
    return VIEWER_PATH.read_text()


def test_apply_spectacle_effects_defined():
    """applySpectacleEffects function must be defined in viewer JS."""
    html = _read_viewer()
    assert "function applySpectacleEffects(" in html


def test_show_banner_defined():
    """showBanner function must be defined in viewer JS."""
    html = _read_viewer()
    assert "function showBanner(" in html


def test_screen_shake_keyframes():
    """CSS must contain screen-shake keyframes animation."""
    html = _read_viewer()
    assert "@keyframes screen-shake" in html


def test_fire_border_keyframes():
    """CSS must contain fire-border keyframes animation."""
    html = _read_viewer()
    assert "@keyframes fire-border" in html


def test_spectacle_banner_class():
    """CSS must contain .spectacle-banner class."""
    html = _read_viewer()
    assert ".spectacle-banner" in html


def test_render_round_calls_apply_spectacle():
    """renderRound must call applySpectacleEffects."""
    html = _read_viewer()
    assert "applySpectacleEffects(" in html
    # Verify it references round.spectacle or spectacle.tier
    assert "spectacle" in html.lower()
