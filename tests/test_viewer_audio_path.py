"""Tests that viewer audio asset paths are correct relative paths."""

from pathlib import Path

from conftest import read_viewer_content

VIEWER_DIR = Path(__file__).resolve().parent.parent / "viewer"


def test_viewer_index_exists() -> None:
    """The viewer index.html file must exist."""
    assert (VIEWER_DIR / "index.html").is_file(), "Expected viewer/index.html to exist"


def test_stinger_paths_use_parent_relative() -> None:
    """Stinger audio paths must use ../audio/assets/ (not bare audio/assets/)."""
    content = read_viewer_content()
    assert "../audio/assets/" in content, (
        "Expected '../audio/assets/' in viewer JS"
    )


def test_no_broken_bare_audio_path() -> None:
    """No bare 'audio/assets/' paths should remain (only ../audio/assets/)."""
    content = read_viewer_content()
    # Remove all correct paths, then check no bare ones remain
    sanitized = content.replace("../audio/assets/", "")
    assert "audio/assets/" not in sanitized, (
        "Found bare 'audio/assets/' path without '../' prefix in viewer JS"
    )
