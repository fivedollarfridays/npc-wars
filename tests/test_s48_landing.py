"""Tests for Kill Switch landing page and root route (T48.1)."""

from pathlib import Path

from fastapi.testclient import TestClient

from server.app import app

STATIC_DIR = Path(__file__).resolve().parent.parent / "server" / "static"

client = TestClient(app)


# ── 1. Static file exists ───────────────────────────────────────────


def test_index_html_exists():
    """server/static/index.html must exist."""
    assert (STATIC_DIR / "index.html").is_file()


def test_index_contains_game_title():
    """Landing page contains 'Kill Switch'."""
    html = (STATIC_DIR / "index.html").read_text()
    assert "Kill Switch" in html or "KILL SWITCH" in html


def test_index_contains_editor_link():
    """Landing page links to the code editor."""
    html = (STATIC_DIR / "index.html").read_text()
    assert "/static/editor.html" in html


def test_index_contains_tournaments_link():
    """Landing page links to tournaments."""
    html = (STATIC_DIR / "index.html").read_text()
    assert "/tournaments" in html


def test_index_contains_leaderboard_link():
    """Landing page links to leaderboard."""
    html = (STATIC_DIR / "index.html").read_text()
    assert "/leaderboard" in html


# ── 2. Root route ───────────────────────────────────────────────────


def test_root_route_returns_200():
    """GET / returns 200."""
    resp = client.get("/")
    assert resp.status_code == 200


def test_root_route_returns_html():
    """GET / returns HTML content."""
    resp = client.get("/")
    assert "text/html" in resp.headers["content-type"]


def test_root_route_contains_kill_switch():
    """GET / response body contains game title."""
    resp = client.get("/")
    text = resp.text
    assert "Kill Switch" in text or "KILL SWITCH" in text
