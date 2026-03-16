"""Tests for dark_entrance spectacle effect (watcher_spawn) in viewer/match.html."""

from pathlib import Path

MATCH_HTML = Path(__file__).resolve().parent.parent / "viewer" / "match.html"


def _read_html() -> str:
    return MATCH_HTML.read_text()


def test_dark_entrance_overlay_css_class_exists():
    html = _read_html()
    assert ".dark-entrance-overlay" in html


def test_watcher_scale_in_keyframes_exists():
    html = _read_html()
    assert "@keyframes watcher-scale-in" in html


def test_dark_entrance_effect_function_exists():
    html = _read_html()
    assert "function darkEntranceEffect()" in html


def test_watcher_spawn_trigger_calls_dark_entrance():
    html = _read_html()
    assert "watcher_spawn" in html
    assert "darkEntranceEffect()" in html


def test_function_creates_overlay_divs():
    html = _read_html()
    assert "dark-entrance-overlay" in html
    assert "createElement('div')" in html or 'createElement("div")' in html


def test_overlay_cleanup_via_remove():
    """Overlay elements must be cleaned up after animation."""
    html = _read_html()
    # Find the darkEntranceEffect function body and check for .remove()
    start = html.index("function darkEntranceEffect()")
    # Look within a reasonable range for cleanup
    chunk = html[start : start + 1500]
    assert ".remove()" in chunk
