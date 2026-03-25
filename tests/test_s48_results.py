"""Tests for results overlay + play-again loop (T48.5)."""

from pathlib import Path

from fastapi.testclient import TestClient

from server.app import app

VIEWER_DIR = Path(__file__).resolve().parent.parent / "viewer"

client = TestClient(app)


# -- 1. Results overlay HTML element exists ----------------------------------


def test_viewer_has_results_overlay_element():
    """Viewer HTML contains a results overlay div."""
    resp = client.get("/viewer")
    assert 'id="results-overlay"' in resp.text


def test_results_overlay_hidden_by_default():
    """Results overlay is hidden by default (display:none)."""
    resp = client.get("/viewer")
    html = resp.text
    # The overlay element should have display:none in its inline style
    idx = html.find('id="results-overlay"')
    assert idx != -1
    # Check surrounding context for display:none
    snippet = html[max(0, idx - 200) : idx + 200]
    assert "display:none" in snippet or "display: none" in snippet


# -- 2. Action buttons / links in overlay ------------------------------------


def test_results_overlay_has_play_again_link():
    """Results overlay has a Play Again link pointing to /static/editor.html."""
    resp = client.get("/viewer")
    html = resp.text
    assert "/static/editor.html" in html


def test_results_overlay_has_leaderboard_link():
    """Results overlay has a Leaderboard link pointing to /leaderboard."""
    resp = client.get("/viewer")
    html = resp.text
    # Find the results overlay section and check for leaderboard link
    idx = html.find('id="results-overlay"')
    assert idx != -1
    overlay_section = html[idx : idx + 2000]
    assert "/leaderboard" in overlay_section


def test_results_overlay_has_watch_again_button():
    """Results overlay has a Watch Again button."""
    resp = client.get("/viewer")
    html = resp.text
    idx = html.find('id="results-overlay"')
    assert idx != -1
    overlay_section = html[idx : idx + 2000]
    assert "watchAgain" in overlay_section or "watch-again" in overlay_section


# -- 3. Results JS module exists and is loaded --------------------------------


def test_results_js_file_exists():
    """viewer/js/results.js exists."""
    results_js = VIEWER_DIR / "js" / "results.js"
    assert results_js.exists(), "viewer/js/results.js should exist"


def test_results_js_referenced_in_viewer_html():
    """Viewer HTML includes a script tag for js/results.js."""
    resp = client.get("/viewer")
    assert "js/results.js" in resp.text


def test_results_js_has_show_results_function():
    """results.js contains a showResultsOverlay function."""
    js = (VIEWER_DIR / "js" / "results.js").read_text()
    assert "showResultsOverlay" in js


def test_results_js_has_hide_results_function():
    """results.js contains a hideResultsOverlay function."""
    js = (VIEWER_DIR / "js" / "results.js").read_text()
    assert "hideResultsOverlay" in js


# -- 4. Integration: showWinner hooks into results overlay -------------------


def test_controls_js_calls_show_results():
    """controls.js showWinner function triggers the results overlay."""
    js = (VIEWER_DIR / "js" / "controls.js").read_text()
    assert "showResultsOverlay" in js


# -- 5. Results content: kill feed + stats sections --------------------------


def test_results_overlay_has_kill_feed_section():
    """Results overlay has a section for kill feed."""
    resp = client.get("/viewer")
    idx = html_find_overlay(resp.text)
    overlay = resp.text[idx : idx + 3000]
    assert "results-kills" in overlay or "results-kill-feed" in overlay


def test_results_overlay_has_stats_section():
    """Results overlay has a section for top stats."""
    resp = client.get("/viewer")
    idx = html_find_overlay(resp.text)
    overlay = resp.text[idx : idx + 3000]
    assert "results-stats" in overlay


def test_results_overlay_has_winner_section():
    """Results overlay has a section displaying the winner."""
    resp = client.get("/viewer")
    idx = html_find_overlay(resp.text)
    overlay = resp.text[idx : idx + 3000]
    assert "results-winner" in overlay


def html_find_overlay(html: str) -> int:
    """Helper: find the start of results-overlay in HTML."""
    idx = html.find('id="results-overlay"')
    assert idx != -1, "results-overlay not found"
    return idx
