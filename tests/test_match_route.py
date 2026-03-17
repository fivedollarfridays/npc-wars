"""Tests for GET /api/match/{match_id} endpoint."""

import json

import pytest
from fastapi.testclient import TestClient

from server.app import app


@pytest.fixture()
def results_dir(tmp_path):
    """Provide a temporary results directory and configure app to use it."""
    app.state.results_dir = str(tmp_path)
    yield tmp_path
    # Reset to default
    app.state.results_dir = "results"


@pytest.fixture()
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_get_existing_match(client, results_dir):
    """GET /api/match/{id} returns 200 with match data for existing match."""
    match_data = {
        "match_id": 1,
        "date": "2026-03-12T22:29:15Z",
        "players": [{"name": "AggroBot"}],
        "rounds": [],
    }
    (results_dir / "match_001.json").write_text(json.dumps(match_data))

    response = client.get("/api/match/001")

    assert response.status_code == 200
    assert response.json() == match_data


def test_get_nonexistent_match(client, results_dir):
    """GET /api/match/{id} returns 404 for missing match."""
    response = client.get("/api/match/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Match not found"}


def test_match_includes_diff_data(client, results_dir):
    """GET /api/match/{id} includes diff data when present in match JSON."""
    match_data = {
        "match_id": 2,
        "players": [{"name": "AggroBot"}],
        "diff": {"AggroBot": {"kills": 3, "deaths": -1}},
    }
    (results_dir / "match_002.json").write_text(json.dumps(match_data))

    response = client.get("/api/match/002")

    assert response.status_code == 200
    body = response.json()
    assert "diff" in body
    assert body["diff"] == {"AggroBot": {"kills": 3, "deaths": -1}}


def test_path_traversal_rejected(client, results_dir):
    """match_id with path traversal characters is rejected."""
    response = client.get("/api/match/..%2F..%2Fetc%2Fpasswd")

    assert response.status_code in (400, 404)


def test_get_match_by_uuid(client, results_dir):
    """GET /api/match/{uuid} finds {uuid}.json for non-numeric IDs."""
    match_data = {"match_id": "abc-123", "players": []}
    (results_dir / "abc-123.json").write_text(json.dumps(match_data))

    response = client.get("/api/match/abc-123")

    assert response.status_code == 200
    assert response.json() == match_data
