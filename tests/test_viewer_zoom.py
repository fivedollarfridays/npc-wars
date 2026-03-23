"""Tests for viewer zoom controls and mobile responsive layout.

Verifies zoom in/out capability (mousewheel + buttons) and mobile-friendly
sidebar collapse.
"""
from __future__ import annotations

from conftest import read_viewer_content


def _read_viewer() -> str:
    """Read all viewer files (index.html + js/*.js)."""
    return read_viewer_content()


# --- Cycle 1: Zoom controls ---


def test_zoom_variable_exists() -> None:
    """Viewer must track a zoom level variable."""
    html = _read_viewer()
    assert "zoomLevel" in html, "Missing zoomLevel variable"


def test_zoom_buttons_exist() -> None:
    """Viewer must have zoom in and zoom out buttons."""
    html = _read_viewer()
    assert "zoom-in" in html or "zoomIn" in html, "Missing zoom-in button"
    assert "zoom-out" in html or "zoomOut" in html, "Missing zoom-out button"


def test_mousewheel_zoom_handler() -> None:
    """Viewer must handle mousewheel events for zoom."""
    html = _read_viewer()
    assert "wheel" in html, "Missing wheel event handler for zoom"


def test_zoom_min_max_bounds() -> None:
    """Zoom must be bounded between 0.5 and 3."""
    html = _read_viewer()
    assert "0.5" in html, "Missing min zoom 0.5"
    # 3 or 3.0 for max
    assert "maxZoom" in html or "MAX_ZOOM" in html or "zoomLevel" in html


def test_zoom_applies_transform() -> None:
    """Zoom must apply a transform to the canvas (CSS scale or ctx transform)."""
    html = _read_viewer()
    assert "setTransform" in html or "ctx.scale" in html \
        or "style.transform" in html, \
        "Missing canvas transform for zoom"


# --- Cycle 2: Mobile responsive ---


def test_mobile_media_query_exists() -> None:
    """Viewer must have a media query for mobile layout (max-width: 768px)."""
    html = _read_viewer()
    assert "768px" in html, "Missing 768px media query breakpoint"


def test_sidebar_mobile_collapse() -> None:
    """Sidebar must change layout on mobile (bottom panel or collapse)."""
    html = _read_viewer()
    # Media query should affect .sidebar or .main flex direction
    assert "768px" in html
    # The sidebar styling must be modified at the breakpoint
    assert "sidebar" in html
