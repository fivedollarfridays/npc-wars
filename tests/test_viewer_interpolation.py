"""Tests for viewer movement interpolation between rounds (T15.8)."""

from __future__ import annotations

import re

from conftest import read_viewer_content


def _read_html() -> str:
    return read_viewer_content()


def _extract_js(html: str) -> str:
    """Return the JS content from the combined viewer files.

    After the modular split, JS is in separate files already included
    in the combined content, so just return the full content.
    """
    return html


# --- Cycle 1: lerp and interpolation state variables ---


def test_lerp_function_exists() -> None:
    """A lerp(a, b, t) function should be defined in the viewer JS."""
    js = _extract_js(_read_html())
    assert re.search(r"function\s+lerp\s*\(", js), "lerp function not found"


def test_prev_positions_variable_exists() -> None:
    """prevPositions state variable should exist for tracking prior positions."""
    js = _extract_js(_read_html())
    assert "prevPositions" in js, "prevPositions variable not found"


def test_interp_duration_variable_exists() -> None:
    """interpDuration variable should exist for controlling animation timing."""
    js = _extract_js(_read_html())
    assert "interpDuration" in js, "interpDuration variable not found"


# --- Cycle 2: Extracted renderCanvas and rAF-based playback ---


def test_render_canvas_function_exists() -> None:
    """renderCanvas should be extracted from renderRound for reuse."""
    js = _extract_js(_read_html())
    assert re.search(r"function\s+renderCanvas\s*\(", js), (
        "renderCanvas function not found"
    )


def test_playback_loop_uses_request_animation_frame() -> None:
    """Playback should use requestAnimationFrame, not just setInterval."""
    js = _extract_js(_read_html())
    assert re.search(r"requestAnimationFrame\s*\(\s*playbackLoop", js), (
        "requestAnimationFrame(playbackLoop) not found"
    )


def test_playback_loop_function_exists() -> None:
    """A playbackLoop function should exist for rAF-based playback."""
    js = _extract_js(_read_html())
    assert re.search(r"function\s+playbackLoop\s*\(", js), (
        "playbackLoop function not found"
    )


# --- Cycle 3: stopPlay cleanup, speed, dead NPC handling ---


def test_stop_play_cancels_animation_frame() -> None:
    """stopPlay should call cancelAnimationFrame to stop the rAF loop."""
    js = _extract_js(_read_html())
    assert "cancelAnimationFrame" in js, "cancelAnimationFrame not found"
    # Verify it's in the context of stopping playback
    stop_match = re.search(
        r"function\s+stopPlay\s*\([^)]*\)\s*\{(.*?)\n\s*\}",
        js,
        re.DOTALL,
    )
    assert stop_match, "stopPlay function not found"
    assert "cancelAnimationFrame" in stop_match.group(1), (
        "cancelAnimationFrame not in stopPlay"
    )


def test_interp_duration_based_on_speed() -> None:
    """interpDuration should be calculated from speed (1000 / speed)."""
    js = _extract_js(_read_html())
    # Should see interpDuration = 1000 / speed somewhere
    assert re.search(r"interpDuration\s*=\s*1000\s*/\s*speed", js), (
        "interpDuration = 1000 / speed not found"
    )


def test_dead_npcs_not_interpolated() -> None:
    """Dead/eliminated NPCs should be excluded from interpolation."""
    js = _extract_js(_read_html())
    # The interpolation logic should check pos.alive before lerping
    # Look for alive check near lerp usage
    assert re.search(r"interpolat", js, re.IGNORECASE), (
        "No interpolation logic found"
    )
    # Find the interpolation function/logic and verify alive check
    # The renderInterpolatedFrame or similar should check alive
    interp_section = re.search(
        r"function\s+renderInterpolatedFrame\s*\([^)]*\)\s*\{(.*?)\n\s*\}",
        js,
        re.DOTALL,
    )
    assert interp_section, "renderInterpolatedFrame function not found"
    body = interp_section.group(1)
    assert "alive" in body, (
        "renderInterpolatedFrame does not check alive status"
    )


def test_store_positions_function_exists() -> None:
    """A storePositions helper should exist for saving round positions."""
    js = _extract_js(_read_html())
    assert re.search(r"function\s+storePositions\s*\(", js), (
        "storePositions function not found"
    )


def test_lerp_clamps_t() -> None:
    """lerp should clamp t to [0, 1] range for safety."""
    js = _extract_js(_read_html())
    lerp_match = re.search(
        r"function\s+lerp\s*\([^)]*\)\s*\{(.*?)\}",
        js,
        re.DOTALL,
    )
    assert lerp_match, "lerp function not found"
    body = lerp_match.group(1)
    # Should use Math.min/Math.max or clamp
    assert "Math.min" in body or "Math.max" in body or "clamp" in body, (
        "lerp does not clamp t value"
    )


def test_set_speed_updates_interp_duration() -> None:
    """setSpeed should update interpDuration for the rAF loop."""
    js = _extract_js(_read_html())
    speed_match = re.search(
        r"function\s+setSpeed\s*\([^)]*\)\s*\{(.*?)\n\s*\}",
        js,
        re.DOTALL,
    )
    assert speed_match, "setSpeed function not found"
    body = speed_match.group(1)
    assert "interpDuration" in body, "setSpeed does not update interpDuration"
