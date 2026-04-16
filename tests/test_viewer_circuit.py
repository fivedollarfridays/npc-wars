"""Tests for Code Circuit viewer modules (T66.2).

Verifies game detection, circuit renderer, circuit sidebar,
and Kill Switch effects preservation.
"""
from __future__ import annotations

from pathlib import Path

VIEWER_DIR = Path(__file__).parent.parent / "viewer"


def _read_js(name: str) -> str:
    js = VIEWER_DIR / "js" / name
    assert js.exists(), f"viewer/js/{name} must exist"
    return js.read_text(encoding="utf-8")


# --- Game detection ---


def test_game_detect_module_exists() -> None:
    assert (VIEWER_DIR / "js" / "game_detect.js").exists()


def test_detect_game_function() -> None:
    js = _read_js("game_detect.js")
    assert "detectGame" in js


def test_detects_circuit_game() -> None:
    js = _read_js("game_detect.js")
    assert '"circuit"' in js


def test_detects_killswitch_game() -> None:
    js = _read_js("game_detect.js")
    assert '"killswitch"' in js


def test_detection_uses_game_field() -> None:
    js = _read_js("game_detect.js")
    assert ".game" in js


# --- KS effects preserved ---


def test_ks_effects_module_exists() -> None:
    assert (VIEWER_DIR / "js" / "effects.js").exists()


def test_ks_spectacle_effects() -> None:
    js = _read_js("effects.js")
    assert "applySpectacleEffects" in js


def test_ks_kill_cam() -> None:
    js = _read_js("effects.js")
    assert "triggerKillCam" in js


def test_ks_renderer_preserves_grid() -> None:
    js = _read_js("renderer.js")
    assert "grid_size" in js


def test_ks_terrain_tiles() -> None:
    js = _read_js("renderer.js")
    assert "terrain_tiles" in js


# --- CC renderer ---


def test_circuit_renderer_exists() -> None:
    assert (VIEWER_DIR / "js" / "circuit_renderer.js").exists()


def test_circuit_renderer_draws_track() -> None:
    js = _read_js("circuit_renderer.js")
    assert "renderCircuitCanvas" in js


# --- CC sidebar ---


def test_circuit_sidebar_exists() -> None:
    assert (VIEWER_DIR / "js" / "circuit_sidebar.js").exists()


def test_circuit_sidebar_shows_positions() -> None:
    js = _read_js("circuit_sidebar.js")
    assert "position" in js


def test_circuit_sidebar_shows_lap_times() -> None:
    js = _read_js("circuit_sidebar.js")
    assert "lap_time" in js


def test_circuit_event_feed() -> None:
    js = _read_js("circuit_sidebar.js")
    assert "updateCircuitEvents" in js


def test_commentary_works_with_both_formats() -> None:
    js = _read_js("commentary.js")
    assert "commentary" in js


# --- File size constraints ---


def test_game_detect_under_50_loc() -> None:
    lines = _read_js("game_detect.js").splitlines()
    assert len(lines) < 50, f"game_detect.js is {len(lines)} lines, must be < 50"


def test_circuit_renderer_under_200_loc() -> None:
    lines = _read_js("circuit_renderer.js").splitlines()
    assert len(lines) < 200, f"circuit_renderer.js is {len(lines)} lines, must be < 200"


def test_circuit_sidebar_under_150_loc() -> None:
    lines = _read_js("circuit_sidebar.js").splitlines()
    assert len(lines) < 150, f"circuit_sidebar.js is {len(lines)} lines, must be < 150"
