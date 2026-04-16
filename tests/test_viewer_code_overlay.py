"""Tests for viewer code overlay panel (T65.3).

Verifies code_overlay.js renders a collapsible panel showing decision traces
alongside the replay, with per-bot toggling, active branch highlighting,
and graceful handling of missing trace data.
"""
from __future__ import annotations

from pathlib import Path

from conftest import read_viewer_content

OVERLAY_JS = Path(__file__).parent.parent / "viewer" / "js" / "code_overlay.js"


def _read_viewer() -> str:
    return read_viewer_content()


# --- File exists and is under 200 LOC ---


def test_code_overlay_file_exists() -> None:
    """code_overlay.js must exist in viewer/js/."""
    assert OVERLAY_JS.exists(), "Missing viewer/js/code_overlay.js"


def test_code_overlay_under_200_loc() -> None:
    """code_overlay.js must be under 200 lines."""
    lines = OVERLAY_JS.read_text().splitlines()
    assert len(lines) < 200, f"code_overlay.js is {len(lines)} lines, must be < 200"


# --- Panel element ---


def test_code_overlay_panel_element() -> None:
    """Viewer must contain a code overlay panel container."""
    html = _read_viewer()
    assert "code-overlay" in html, "Missing code overlay panel element"


def test_code_overlay_collapsible() -> None:
    """Panel must be collapsible (toggle function or collapsed class)."""
    html = _read_viewer()
    assert "toggleCodeOverlay" in html or "collapsed" in html, \
        "Code overlay must be collapsible"


# --- Decision trace rendering ---


def test_render_decision_trace_function() -> None:
    """Must define a renderDecisionTrace function."""
    html = _read_viewer()
    assert "renderDecisionTrace" in html, "Missing renderDecisionTrace function"


def test_branch_taken_highlight() -> None:
    """Active branch must be highlighted (active class or style)."""
    html = _read_viewer()
    assert "trace-active" in html or "branch-active" in html, \
        "Missing active branch highlighting"


def test_inactive_branch_dimmed() -> None:
    """Inactive branches must be dimmed."""
    html = _read_viewer()
    assert "trace-inactive" in html or "branch-inactive" in html, \
        "Missing inactive branch dimming"


# --- Per-bot toggling ---


def test_per_bot_trace_toggle() -> None:
    """Must support toggling trace display per bot."""
    html = _read_viewer()
    assert "trace-toggle" in html or "toggleBotTrace" in html, \
        "Missing per-bot trace toggle"


# --- Graceful no-data handling ---


def test_no_trace_data_hidden() -> None:
    """Panel must hide when no trace data is present."""
    html = _read_viewer()
    assert "decision_traces" in html, \
        "Must check for decision_traces in round data"


# --- Round change integration ---


def test_update_code_overlay_function() -> None:
    """Must define an updateCodeOverlay function for round sync."""
    html = _read_viewer()
    assert "updateCodeOverlay" in html, "Missing updateCodeOverlay function"


def test_code_overlay_called_in_render_round() -> None:
    """renderRound must call updateCodeOverlay."""
    js = (Path(__file__).parent.parent / "viewer" / "js" / "renderer.js").read_text()
    assert "updateCodeOverlay" in js, "updateCodeOverlay not wired into renderRound"
