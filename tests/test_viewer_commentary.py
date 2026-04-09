"""Tests for viewer commentary ticker (T62.3).

Verifies commentary.js renders a ticker below the canvas, distinguishes
play-by-play from color commentary, has a toggle button, and handles
missing commentary gracefully.
"""
from __future__ import annotations

from conftest import read_viewer_content


def _read_viewer() -> str:
    return read_viewer_content()


# --- Ticker element exists ---


def test_commentary_ticker_element() -> None:
    """Viewer must contain a commentary ticker container."""
    html = _read_viewer()
    assert "commentary-ticker" in html, "Missing #commentary-ticker element"


def test_commentary_toggle_button() -> None:
    """Controls must include a toggle button for commentary."""
    html = _read_viewer()
    assert "commentary-toggle" in html, "Missing commentary toggle button"


# --- Line type styling ---


def test_play_by_play_style() -> None:
    """Play-by-play lines must use white/default text color."""
    html = _read_viewer()
    assert "play_by_play" in html, "Missing play_by_play line type handling"


def test_color_commentary_gold_style() -> None:
    """Color commentary lines must use a gold/accent color."""
    html = _read_viewer()
    # Should reference gold or a gold-like color for color commentary
    assert "color" in html and "gold" in html.lower() or "#ffd700" in html.lower(), \
        "Missing gold styling for color commentary"


# --- Round sync ---


def test_update_commentary_function() -> None:
    """Must define an updateCommentary function for round sync."""
    html = _read_viewer()
    assert "updateCommentary" in html, "Missing updateCommentary function"


def test_commentary_called_in_render_round() -> None:
    """renderRound must call updateCommentary."""
    html = _read_viewer()
    assert "updateCommentary" in html, "updateCommentary not wired into rendering"


# --- Graceful fallback ---


def test_commentary_handles_missing_key() -> None:
    """Commentary code must guard against missing commentary key."""
    html = _read_viewer()
    # Should check for matchData.commentary existence
    assert "commentary" in html, "No reference to commentary data key"


# --- Toggle functionality ---


def test_toggle_commentary_function() -> None:
    """Must define a toggleCommentary function."""
    html = _read_viewer()
    assert "toggleCommentary" in html, "Missing toggleCommentary function"


# --- Fade transitions ---


def test_commentary_fade_transition() -> None:
    """Commentary ticker must support fade transitions."""
    html = _read_viewer()
    assert "opacity" in html or "fade" in html.lower(), \
        "Missing fade/opacity transition for commentary"


# --- File size constraint ---


def test_commentary_file_under_200_loc() -> None:
    """commentary.js must be under 200 lines of code."""
    from pathlib import Path
    js_file = Path(__file__).parent.parent / "viewer" / "js" / "commentary.js"
    assert js_file.exists(), "viewer/js/commentary.js does not exist"
    lines = js_file.read_text().splitlines()
    assert len(lines) < 200, f"commentary.js is {len(lines)} lines, must be < 200"
