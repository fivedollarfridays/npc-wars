"""Tests that viewer audio asset paths are correct relative paths."""

from pathlib import Path

VIEWER_HTML = Path(__file__).resolve().parent.parent / "viewer" / "match.html"


def test_viewer_html_exists() -> None:
    """The viewer file must exist."""
    assert VIEWER_HTML.is_file(), f"Expected {VIEWER_HTML} to exist"


def test_stinger_paths_use_parent_relative() -> None:
    """Stinger audio paths must use ../audio/assets/ (not bare audio/assets/)."""
    content = VIEWER_HTML.read_text()
    assert "../audio/assets/" in content, (
        "Expected '../audio/assets/' in viewer/match.html"
    )


def test_no_broken_bare_audio_path() -> None:
    """No bare 'audio/assets/' paths should remain (only ../audio/assets/)."""
    content = VIEWER_HTML.read_text()
    # Remove all correct paths, then check no bare ones remain
    sanitized = content.replace("../audio/assets/", "")
    assert "audio/assets/" not in sanitized, (
        "Found bare 'audio/assets/' path without '../' prefix in viewer/match.html"
    )
