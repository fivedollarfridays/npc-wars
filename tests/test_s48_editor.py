"""Tests for T48.3: Editor lobby integration — real polling, localStorage, redirect."""

from pathlib import Path

EDITOR_PATH = Path(__file__).resolve().parent.parent / "server" / "static" / "editor.html"


def _read_editor() -> str:
    return EDITOR_PATH.read_text()


# --- localStorage save/load ---


def test_editor_saves_bot_source_to_localstorage():
    """On submit, editor saves code to localStorage."""
    html = _read_editor()
    assert "localStorage.setItem" in html
    assert "lastBotSource" in html


def test_editor_loads_bot_source_from_localstorage():
    """On page load, editor pre-fills from localStorage."""
    html = _read_editor()
    assert "localStorage.getItem" in html
    assert "lastBotSource" in html


# --- Real lobby polling ---


def test_editor_polls_lobby_status_api():
    """After submit, editor polls /api/lobby/status."""
    html = _read_editor()
    assert "/api/lobby/status" in html


def test_editor_uses_setinterval_for_polling():
    """Editor uses setInterval for periodic polling."""
    html = _read_editor()
    assert "setInterval" in html


def test_editor_polls_every_2_seconds():
    """Polling interval is 2000ms."""
    html = _read_editor()
    assert "2000" in html


# --- No fake countdown ---


def test_editor_no_hardcoded_countdown_30():
    """Editor no longer has the fake 'countdown = 30' pattern."""
    html = _read_editor()
    assert "countdown = 30" not in html
    assert "countdown--" not in html


# --- Player list display ---


def test_editor_shows_player_list():
    """Editor displays player_list from status response."""
    html = _read_editor()
    assert "player_list" in html


def test_editor_shows_player_count():
    """Editor shows player count (e.g. X/8 format)."""
    html = _read_editor()
    # Should reference .players and .max from status
    assert ".players" in html
    assert ".max" in html


# --- Redirect to viewer ---


def test_editor_redirects_to_viewer():
    """When match_id appears, editor redirects to /viewer."""
    html = _read_editor()
    assert "/viewer?match=" in html


def test_editor_checks_match_id_in_response():
    """Editor checks for match_id in lobby status response."""
    html = _read_editor()
    assert "match_id" in html


# --- Double-submit prevention ---


def test_editor_disables_button_during_polling():
    """Submit button is disabled during lobby polling."""
    html = _read_editor()
    # Button should be disabled after submit and during polling
    assert "disabled = true" in html or "disabled=true" in html or ".disabled = true" in html


# --- Time remaining display ---


def test_editor_shows_time_remaining():
    """Editor displays time_remaining from status."""
    html = _read_editor()
    assert "time_remaining" in html
