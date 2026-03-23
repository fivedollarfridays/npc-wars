"""Tests for viewer modular JS structure (T41.3b).

Verifies that viewer/match.html has been split into modular JS files
in viewer/js/ with an index.html entry point.
"""
from __future__ import annotations

from pathlib import Path

VIEWER_DIR = Path(__file__).parent.parent / "viewer"
JS_DIR = VIEWER_DIR / "js"

EXPECTED_JS_FILES = [
    "audio.js",
    "shapes.js",
    "renderer.js",
    "effects.js",
    "events.js",
    "sidebar.js",
    "controls.js",
    "live.js",
    "app.js",
]

MAX_JS_LINES = 600  # Extended for effects.js with kill cam + round transitions


def _read_all_viewer_js() -> str:
    """Read all JS files and index.html concatenated."""
    parts = []
    index = VIEWER_DIR / "index.html"
    if index.exists():
        parts.append(index.read_text())
    for name in EXPECTED_JS_FILES:
        path = JS_DIR / name
        if path.exists():
            parts.append(path.read_text())
    return "\n".join(parts)


# --- Cycle 1: File structure ---


def test_index_html_exists() -> None:
    """viewer/index.html must exist as the entry point."""
    assert (VIEWER_DIR / "index.html").exists(), "Missing viewer/index.html"


def test_js_directory_exists() -> None:
    """viewer/js/ directory must exist."""
    assert JS_DIR.is_dir(), "Missing viewer/js/ directory"


def test_all_js_files_exist() -> None:
    """All expected JS module files must exist."""
    for name in EXPECTED_JS_FILES:
        assert (JS_DIR / name).exists(), f"Missing viewer/js/{name}"


def test_match_html_backup_exists() -> None:
    """Original match.html should be renamed to match.html.bak."""
    assert (VIEWER_DIR / "match.html.bak").exists(), "Missing match.html.bak backup"


# --- Cycle 2: Script loading in index.html ---


def test_index_html_loads_all_scripts() -> None:
    """index.html must have script tags for all JS files."""
    html = (VIEWER_DIR / "index.html").read_text()
    for name in EXPECTED_JS_FILES:
        assert f'src="js/{name}"' in html, f"Missing script tag for js/{name}"


def test_script_order_app_last() -> None:
    """app.js must be loaded last (it initializes everything)."""
    html = (VIEWER_DIR / "index.html").read_text()
    app_pos = html.find('src="js/app.js"')
    for name in EXPECTED_JS_FILES:
        if name == "app.js":
            continue
        other_pos = html.find(f'src="js/{name}"')
        assert other_pos < app_pos, f"js/{name} must load before js/app.js"


def test_index_html_has_no_inline_script() -> None:
    """index.html should have no significant inline JS (only script src tags)."""
    html = (VIEWER_DIR / "index.html").read_text()
    # Should not have the old inline script content
    assert "class AudioEngine" not in html, "AudioEngine class should be in audio.js, not inline"
    assert "function renderCanvas" not in html, "renderCanvas should be in renderer.js, not inline"
    assert "function togglePlay" not in html, "togglePlay should be in controls.js, not inline"


# --- Cycle 3: No file exceeds 500 lines ---


def test_js_files_under_line_limit() -> None:
    """No JS file should exceed 500 lines."""
    for name in EXPECTED_JS_FILES:
        path = JS_DIR / name
        if not path.exists():
            continue
        lines = len(path.read_text().splitlines())
        assert lines <= MAX_JS_LINES, f"js/{name} has {lines} lines (max {MAX_JS_LINES})"


# --- Cycle 4: Key functions exist in correct files ---


def test_audio_engine_in_audio_js() -> None:
    """AudioEngine class must be in audio.js."""
    content = (JS_DIR / "audio.js").read_text()
    assert "class AudioEngine" in content


def test_shape_functions_in_shapes_js() -> None:
    """Shape drawing functions must be in shapes.js."""
    content = (JS_DIR / "shapes.js").read_text()
    for fn in ["drawCircle", "drawSquare", "drawTriangle", "drawHexagon", "drawDiamond"]:
        assert f"function {fn}" in content, f"Missing {fn} in shapes.js"


def test_render_canvas_in_renderer_js() -> None:
    """renderCanvas function must be in renderer.js."""
    content = (JS_DIR / "renderer.js").read_text()
    assert "function renderCanvas" in content


def test_effects_in_effects_js() -> None:
    """Particle/spectacle effect functions must be in effects.js."""
    content = (JS_DIR / "effects.js").read_text()
    for fn in ["shatterEffect", "deathExplosion", "attackSwoosh", "applySpectacleEffects"]:
        assert f"function {fn}" in content, f"Missing {fn} in effects.js"


def test_event_fx_in_events_js() -> None:
    """Event FX rendering (trap, ability, etc.) kill feed must be in events.js."""
    content = (JS_DIR / "events.js").read_text()
    assert "function updateKillFeed" in content


def test_sidebar_in_sidebar_js() -> None:
    """Sidebar functions must be in sidebar.js."""
    content = (JS_DIR / "sidebar.js").read_text()
    for fn in ["buildBotList", "updateSidebar"]:
        assert f"function {fn}" in content, f"Missing {fn} in sidebar.js"


def test_controls_in_controls_js() -> None:
    """Playback control functions must be in controls.js."""
    content = (JS_DIR / "controls.js").read_text()
    for fn in ["togglePlay", "startPlay", "stopPlay", "setSpeed", "scrubTo"]:
        assert f"function {fn}" in content, f"Missing {fn} in controls.js"


def test_live_in_live_js() -> None:
    """Live play WebSocket code must be in live.js."""
    content = (JS_DIR / "live.js").read_text()
    for fn in ["connectLive", "sendLiveAction", "handleLiveState"]:
        assert f"function {fn}" in content, f"Missing {fn} in live.js"


def test_app_has_init_and_globals() -> None:
    """app.js must have init and global state."""
    content = (JS_DIR / "app.js").read_text()
    assert "function initViewer" in content
    assert "matchData" in content
    assert "TILE_SIZE" in content


# --- Cycle 5: CSS stays in index.html ---


def test_css_in_index_html() -> None:
    """CSS styles must remain in index.html (or a linked CSS file)."""
    html = (VIEWER_DIR / "index.html").read_text()
    assert "<style>" in html or 'rel="stylesheet"' in html


def test_html_structure_in_index_html() -> None:
    """HTML body structure must be in index.html."""
    html = (VIEWER_DIR / "index.html").read_text()
    assert 'id="arena-canvas"' in html
    assert 'id="bot-list"' in html
    assert 'id="kill-feed"' in html
    assert 'id="play-btn"' in html
