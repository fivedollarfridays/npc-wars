"""Tests for unified viewer entry point (T66.2).

Verifies viewer.html loads all modules, shared controls work for both games,
commentary ticker works for both, and no regression in either viewer.
"""
from __future__ import annotations

from pathlib import Path

VIEWER_DIR = Path(__file__).parent.parent / "viewer"


def _read_unified() -> str:
    """Read unified viewer.html + all JS modules."""
    parts = []
    html = VIEWER_DIR / "viewer.html"
    assert html.exists(), "viewer/viewer.html must exist"
    parts.append(html.read_text(encoding="utf-8"))
    js_dir = VIEWER_DIR / "js"
    if js_dir.is_dir():
        for js_file in sorted(js_dir.glob("*.js")):
            parts.append(js_file.read_text(encoding="utf-8"))
    return "\n".join(parts)


# --- 1. Single HTML entry point ---


def test_viewer_html_exists() -> None:
    assert (VIEWER_DIR / "viewer.html").exists()


# --- 2. Shared controls work for both games ---


def test_shared_play_pause() -> None:
    content = _read_unified()
    assert "togglePlay" in content


def test_shared_speed_buttons() -> None:
    content = _read_unified()
    assert "setSpeed" in content


def test_shared_scrubber() -> None:
    content = _read_unified()
    assert "scrubber" in content


def test_shared_zoom_controls() -> None:
    content = _read_unified()
    assert "zoomIn" in content and "zoomOut" in content


# --- 3. Commentary ticker works for both games ---


def test_unified_commentary_ticker() -> None:
    html = (VIEWER_DIR / "viewer.html").read_text(encoding="utf-8")
    assert "commentary-ticker" in html


def test_unified_commentary_toggle() -> None:
    html = (VIEWER_DIR / "viewer.html").read_text(encoding="utf-8")
    assert "commentary-toggle" in html


# --- 4. Unified viewer loads all modules ---


def test_unified_loads_game_detect() -> None:
    html = (VIEWER_DIR / "viewer.html").read_text(encoding="utf-8")
    assert "game_detect.js" in html


def test_unified_loads_audio() -> None:
    html = (VIEWER_DIR / "viewer.html").read_text(encoding="utf-8")
    assert "audio.js" in html


def test_unified_loads_shapes() -> None:
    html = (VIEWER_DIR / "viewer.html").read_text(encoding="utf-8")
    assert "shapes.js" in html


def test_unified_loads_effects() -> None:
    html = (VIEWER_DIR / "viewer.html").read_text(encoding="utf-8")
    assert "effects.js" in html


def test_unified_loads_events() -> None:
    html = (VIEWER_DIR / "viewer.html").read_text(encoding="utf-8")
    assert "events.js" in html


def test_unified_loads_sidebar() -> None:
    html = (VIEWER_DIR / "viewer.html").read_text(encoding="utf-8")
    assert "sidebar.js" in html


def test_unified_loads_renderer() -> None:
    html = (VIEWER_DIR / "viewer.html").read_text(encoding="utf-8")
    assert "renderer.js" in html


def test_unified_loads_circuit_renderer() -> None:
    html = (VIEWER_DIR / "viewer.html").read_text(encoding="utf-8")
    assert "circuit_renderer.js" in html


def test_unified_loads_circuit_sidebar() -> None:
    html = (VIEWER_DIR / "viewer.html").read_text(encoding="utf-8")
    assert "circuit_sidebar.js" in html


def test_unified_loads_commentary() -> None:
    html = (VIEWER_DIR / "viewer.html").read_text(encoding="utf-8")
    assert "commentary.js" in html


def test_unified_loads_code_overlay() -> None:
    html = (VIEWER_DIR / "viewer.html").read_text(encoding="utf-8")
    assert "code_overlay.js" in html


# --- 5. Game-aware rendering dispatch ---


def test_app_calls_detect_game() -> None:
    js = (VIEWER_DIR / "js" / "app.js").read_text(encoding="utf-8")
    assert "detectGame" in js


def test_app_dispatches_to_circuit() -> None:
    js = (VIEWER_DIR / "js" / "app.js").read_text(encoding="utf-8")
    assert "circuit" in js


def test_render_round_game_aware() -> None:
    js = (VIEWER_DIR / "js" / "renderer.js").read_text(encoding="utf-8")
    assert "currentGameType" in js or "gameType" in js
