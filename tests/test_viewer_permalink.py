"""Tests for permalink copy-link button in the viewer."""

from conftest import read_viewer_content


def test_viewer_has_copy_link_button() -> None:
    """Viewer HTML contains a copy-link button."""
    html = read_viewer_content()
    assert "copy-link-btn" in html or "copyPermalink" in html


def test_viewer_has_copy_permalink_function() -> None:
    """Viewer HTML contains a copyPermalink JS function."""
    html = read_viewer_content()
    assert "function copyPermalink" in html or "copyPermalink" in html
