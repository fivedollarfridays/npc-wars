"""Tests for T51.5: Mobile responsive CSS + desktop-preferred banner."""

from pathlib import Path

import pytest

STATIC_DIR = Path("server/static")
HTML_FILES = [
    "index.html",
    "editor.html",
    "leaderboard.html",
    "profile.html",
    "tournaments.html",
    "tournament.html",
    "store.html",
    "guide.html",
]


@pytest.mark.parametrize("filename", HTML_FILES)
def test_has_viewport_meta(filename: str) -> None:
    content = (STATIC_DIR / filename).read_text()
    assert 'name="viewport"' in content


@pytest.mark.parametrize("filename", HTML_FILES)
def test_links_responsive_css(filename: str) -> None:
    content = (STATIC_DIR / filename).read_text()
    assert "responsive.css" in content


@pytest.mark.parametrize("filename", HTML_FILES)
def test_has_media_query_via_css(filename: str) -> None:
    """Shared responsive.css must contain media queries."""
    css = (STATIC_DIR / "css" / "responsive.css").read_text()
    assert "@media" in css


@pytest.mark.parametrize("filename", HTML_FILES)
def test_has_mobile_banner(filename: str) -> None:
    content = (STATIC_DIR / filename).read_text()
    assert "mobile-banner" in content


def test_banner_is_dismissable() -> None:
    """Index page has localStorage dismiss logic via mobile-banner.js."""
    js = (STATIC_DIR / "js" / "mobile-banner.js").read_text()
    assert "localStorage" in js
    assert "dismiss" in js.lower() or "close" in js.lower()


@pytest.mark.parametrize("filename", HTML_FILES)
def test_loads_mobile_banner_js(filename: str) -> None:
    content = (STATIC_DIR / filename).read_text()
    assert "mobile-banner.js" in content


def test_responsive_css_has_table_wrap() -> None:
    css = (STATIC_DIR / "css" / "responsive.css").read_text()
    assert "table-wrap" in css


def test_responsive_css_has_small_breakpoint() -> None:
    css = (STATIC_DIR / "css" / "responsive.css").read_text()
    assert "480px" in css


def test_editor_banner_mentions_code() -> None:
    """Editor page banner should mention code/desktop editing."""
    content = (STATIC_DIR / "editor.html").read_text()
    # The banner text should be specific to code editing
    assert "Code editing" in content or "code editing" in content


def test_leaderboard_table_wrap() -> None:
    """Leaderboard should wrap its table for mobile scroll."""
    content = (STATIC_DIR / "leaderboard.html").read_text()
    assert "table-wrap" in content
