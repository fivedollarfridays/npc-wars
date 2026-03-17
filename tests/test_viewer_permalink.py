"""Tests for permalink copy-link button in the viewer HTML."""

from pathlib import Path


VIEWER_HTML = Path(__file__).resolve().parent.parent / "viewer" / "match.html"


def test_viewer_has_copy_link_button() -> None:
    """Viewer HTML contains a copy-link button."""
    html = VIEWER_HTML.read_text(encoding="utf-8")
    assert "copy-link-btn" in html or "copyPermalink" in html


def test_viewer_has_copy_permalink_function() -> None:
    """Viewer HTML contains a copyPermalink JS function."""
    html = VIEWER_HTML.read_text(encoding="utf-8")
    assert "function copyPermalink" in html or "copyPermalink" in html
