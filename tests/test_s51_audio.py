"""Tests for T51.2: Audio user gesture fix."""

from pathlib import Path

from fastapi.testclient import TestClient

from server.app import app

VIEWER_DIR = Path(__file__).resolve().parent.parent / "viewer"
AUDIO_JS = VIEWER_DIR / "js" / "audio.js"

client = TestClient(app)


# -- 1. Viewer page loads with audio references ------------------------------


def test_viewer_page_loads() -> None:
    """GET /viewer returns 200 and contains audio.js script reference."""
    resp = client.get("/viewer")
    assert resp.status_code == 200
    assert "audio.js" in resp.text


# -- 2. Audio gesture hint element -------------------------------------------


def test_viewer_has_audio_gesture_hint() -> None:
    """Viewer HTML contains the audio-gesture-hint element."""
    resp = client.get("/viewer")
    assert "audio-gesture-hint" in resp.text


# -- 3. AudioContext not created immediately in init() -----------------------


def test_audio_js_no_immediate_context_in_init() -> None:
    """init() must NOT directly create AudioContext; that belongs in _createContext."""
    source = AUDIO_JS.read_text()

    # Split out the init() method body (from 'init()' to the next method)
    lines = source.split("\n")
    in_init = False
    init_body: list[str] = []
    for line in lines:
        if "init()" in line and "_" not in line:
            in_init = True
            continue
        if in_init:
            # Stop at next method definition (non-indented or single-indent method)
            stripped = line.lstrip()
            if stripped and not line.startswith("  ") and not line.startswith("\t"):
                break
            # Also stop at next method like _createContext or loadStinger
            if (stripped.startswith("_createContext") or
                    stripped.startswith("async ") or
                    stripped.startswith("play(") or
                    stripped.startswith("loadStinger")):
                break
            init_body.append(line)

    # Filter out comment lines before checking
    init_code = [line for line in init_body if not line.lstrip().startswith("//")]
    init_text = "\n".join(init_code)
    assert "AudioContext" not in init_text, (
        "init() should not create AudioContext directly — use _createContext"
    )


def test_audio_js_has_create_context_method() -> None:
    """audio.js must have a _createContext method that creates the AudioContext."""
    source = AUDIO_JS.read_text()
    assert "_createContext" in source, "Missing _createContext method"
    assert "window.AudioContext" in source or "window.webkitAudioContext" in source, (
        "AudioContext must be created somewhere (in _createContext)"
    )


def test_audio_js_play_guards_no_context() -> None:
    """play() and playSynth() should guard against missing ctx."""
    source = AUDIO_JS.read_text()

    # Find play() method - should check for !this.ctx or !this.ready
    lines = source.split("\n")
    in_play = False
    play_first_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("play(") and "playSynth" not in stripped:
            in_play = True
            continue
        if in_play:
            play_first_lines.append(stripped)
            if len(play_first_lines) >= 3:
                break

    play_guard = " ".join(play_first_lines)
    assert "!this.ctx" in play_guard or "!this.ready" in play_guard, (
        "play() must guard against missing audio context"
    )
