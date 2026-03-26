"""Tests for T51.4: Lobby waiting UX enhancements in editor.html."""

from fastapi.testclient import TestClient

from server.app import app

client = TestClient(app)


def test_editor_loads():
    """Editor page returns 200."""
    resp = client.get("/static/editor.html")
    assert resp.status_code == 200


def test_lobby_css_loads():
    """Lobby CSS file loads and contains animations."""
    resp = client.get("/static/css/lobby.css")
    assert resp.status_code == 200
    assert "@keyframes" in resp.text
    assert "pulse" in resp.text


def test_lobby_css_has_match_starting():
    """Lobby CSS contains match-starting animation class."""
    resp = client.get("/static/css/lobby.css")
    assert "match-starting" in resp.text


def test_lobby_js_loads():
    """Lobby JS file loads and contains polling functions."""
    resp = client.get("/static/js/lobby.js")
    assert resp.status_code == 200
    assert "startLobbyPolling" in resp.text
    assert "updateLobbyUI" in resp.text


def test_editor_links_lobby_css():
    """Editor references the external lobby CSS."""
    resp = client.get("/static/editor.html")
    assert "lobby.css" in resp.text


def test_editor_links_lobby_js():
    """Editor references the external lobby JS."""
    resp = client.get("/static/editor.html")
    assert "lobby.js" in resp.text


def test_editor_has_lobby_panel():
    """Editor has a lobby-panel element for enhanced lobby display."""
    resp = client.get("/static/editor.html")
    assert "lobby-panel" in resp.text


def test_editor_has_player_grid():
    """Editor has a player grid for displaying lobby participants."""
    resp = client.get("/static/editor.html")
    assert "lobby-player" in resp.text


def test_editor_has_countdown_element():
    """Editor has a countdown or progress element for lobby waiting."""
    resp = client.get("/static/editor.html")
    text = resp.text.lower()
    assert "countdown" in text or "progress" in text
