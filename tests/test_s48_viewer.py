"""Tests for viewer route + match path resolution (T48.4)."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.app import app

VIEWER_DIR = Path(__file__).resolve().parent.parent / "viewer"

client = TestClient(app)

_MATCH_FIXTURE = {
    "match_id": 42,
    "grid_size": 10,
    "duration_rounds": 5,
    "players": [{"name": "bot_a", "emoji": "A"}],
    "rounds": [],
}


@pytest.fixture()
def _results_dir(tmp_path: Path):
    """Create a temp results dir with a fixture match file."""
    match_file = tmp_path / "match_42.json"
    match_file.write_text(json.dumps(_MATCH_FIXTURE))
    uuid_file = tmp_path / "abc-def-123.json"
    uuid_file.write_text(json.dumps({**_MATCH_FIXTURE, "match_id": "abc-def-123"}))
    old = app.state.results_dir
    app.state.results_dir = str(tmp_path)
    yield tmp_path
    app.state.results_dir = old


# -- 1. GET /viewer route -------------------------------------------------


def test_viewer_route_returns_200():
    """GET /viewer returns 200."""
    resp = client.get("/viewer")
    assert resp.status_code == 200


def test_viewer_route_returns_html():
    """GET /viewer returns HTML content type."""
    resp = client.get("/viewer")
    assert "text/html" in resp.headers["content-type"]


def test_viewer_html_contains_js_app_script():
    """Viewer HTML includes js/app.js script tag."""
    resp = client.get("/viewer")
    assert "js/app.js" in resp.text


# -- 2. Match API endpoint ------------------------------------------------


def test_match_api_numeric_id(_results_dir: Path):
    """GET /api/match/42 returns match JSON for numeric ID."""
    resp = client.get("/api/match/42")
    assert resp.status_code == 200
    data = resp.json()
    assert data["match_id"] == 42


def test_match_api_uuid_id(_results_dir: Path):
    """GET /api/match/{uuid} returns match JSON for UUID format."""
    resp = client.get("/api/match/abc-def-123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["match_id"] == "abc-def-123"


def test_match_api_not_found(_results_dir: Path):
    """GET /api/match/{nonexistent} returns 404."""
    resp = client.get("/api/match/999999")
    assert resp.status_code == 404


# -- 3. Viewer JS match path validation -----------------------------------


def test_viewer_js_validates_file_paths():
    """app.js validateMatchPath accepts results/match_NNN.json format."""
    js = (VIEWER_DIR / "js" / "app.js").read_text()
    assert "validateMatchPath" in js
    # The regex should still accept the classic file path format
    assert "results" in js


def test_viewer_js_supports_api_loading():
    """app.js contains API match loading path for match IDs."""
    js = (VIEWER_DIR / "js" / "app.js").read_text()
    assert "/api/match/" in js


def test_viewer_js_has_match_id_detection():
    """app.js detects match IDs (non-file-path values) and loads via API."""
    js = (VIEWER_DIR / "js" / "app.js").read_text()
    # Should have a function or logic branch for isMatchId / match ID detection
    assert "isMatchId" in js or "loadMatchById" in js
