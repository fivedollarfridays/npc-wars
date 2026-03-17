"""Tests for permalink sharing route: GET /m/{match_id}."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.app import app

SAMPLE_MATCH = {
    "match_id": 42,
    "winner": "AggroBot",
    "duration_rounds": 15,
    "players": [
        {"name": "AggroBot", "emoji": "A"},
        {"name": "TankBot", "emoji": "T"},
    ],
}


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    """Create a test client with a temp results dir containing a sample match."""
    match_file = tmp_path / "match_42.json"
    match_file.write_text(json.dumps(SAMPLE_MATCH), encoding="utf-8")
    app.state.results_dir = str(tmp_path)
    return TestClient(app)


def test_share_existing_match_returns_200(client: TestClient) -> None:
    """GET /m/42 returns 200 with HTML content."""
    resp = client.get("/m/42", follow_redirects=False)
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_share_has_og_title(client: TestClient) -> None:
    """Response includes og:title meta tag with match info."""
    resp = client.get("/m/42", follow_redirects=False)
    body = resp.text
    assert 'og:title' in body
    assert "NPC Wars Match #42" in body


def test_share_has_og_description(client: TestClient) -> None:
    """Response includes og:description with winner and stats."""
    resp = client.get("/m/42", follow_redirects=False)
    body = resp.text
    assert 'og:description' in body
    assert "AggroBot wins" in body
    assert "2 bots" in body
    assert "15 rounds" in body


def test_share_has_redirect_to_viewer(client: TestClient) -> None:
    """Response includes meta refresh redirect to the viewer."""
    resp = client.get("/m/42", follow_redirects=False)
    body = resp.text
    assert "match=42" in body


def test_share_404_for_missing_match(client: TestClient) -> None:
    """GET /m/999 returns 404 when match file doesn't exist."""
    resp = client.get("/m/999", follow_redirects=False)
    assert resp.status_code == 404


def test_share_invalid_id_returns_400(client: TestClient) -> None:
    """Match IDs with special characters return 400."""
    resp = client.get("/m/foo%20bar%3B%3Bdrop", follow_redirects=False)
    assert resp.status_code == 400
