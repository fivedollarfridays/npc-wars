"""Tests for GET /api/match/{match_id}/stream SSE endpoint."""

import json

import pytest
from fastapi.testclient import TestClient

from server.app import app


@pytest.fixture()
def results_dir(tmp_path):
    """Provide a temporary results directory and configure app to use it."""
    app.state.results_dir = str(tmp_path)
    yield tmp_path
    app.state.results_dir = "results"


@pytest.fixture()
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture()
def sample_match():
    """Minimal match data with two rounds."""
    return {
        "match_id": 1,
        "winner": "AggroBot",
        "duration_rounds": 2,
        "rounds": [
            {"round": 1, "positions": [{"name": "AggroBot", "hp": 100}]},
            {"round": 2, "positions": [{"name": "AggroBot", "hp": 80}]},
        ],
    }


# --- Cycle 1: Error paths ---


def test_stream_404_for_missing_match(client, results_dir):
    """Streaming a non-existent match returns 404."""
    response = client.get("/api/match/999/stream")

    assert response.status_code == 404
    assert response.json() == {"detail": "Match not found"}


def test_stream_invalid_id_rejected(client, results_dir):
    """Match IDs with special characters are rejected."""
    response = client.get("/api/match/bad!id/stream")

    assert response.status_code == 400
    assert "Invalid match ID" in response.json()["detail"]


# --- Cycle 2: SSE basics ---


def test_stream_returns_sse_content_type(client, results_dir, sample_match):
    """Stream endpoint returns text/event-stream content type."""
    (results_dir / "match_001.json").write_text(json.dumps(sample_match))

    response = client.get("/api/match/001/stream")

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]


def test_stream_has_retry_field(client, results_dir, sample_match):
    """SSE stream includes a retry directive for auto-reconnect."""
    (results_dir / "match_001.json").write_text(json.dumps(sample_match))

    response = client.get("/api/match/001/stream")

    assert "retry:" in response.text


# --- Cycle 3: SSE event content ---


def test_stream_emits_round_events(client, results_dir, sample_match):
    """Each round in the match is emitted as an 'event: round' SSE event."""
    (results_dir / "match_001.json").write_text(json.dumps(sample_match))

    response = client.get("/api/match/001/stream")
    text = response.text

    assert text.count("event: round") == 2
    # Verify round data is valid JSON in data fields following 'event: round'
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line == "event: round":
            data_line = lines[i + 1]
            payload = json.loads(data_line[len("data: "):])
            assert "round" in payload


def test_stream_emits_complete_event(client, results_dir, sample_match):
    """Stream sends an 'event: complete' with winner and duration."""
    (results_dir / "match_001.json").write_text(json.dumps(sample_match))

    response = client.get("/api/match/001/stream")
    text = response.text

    assert "event: complete" in text
    # Extract complete event data
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line == "event: complete":
            data_line = lines[i + 1]
            payload = json.loads(data_line[len("data: "):])
            assert payload["winner"] == "AggroBot"
            assert payload["duration_rounds"] == 2
            break
    else:
        pytest.fail("No 'event: complete' found in stream")
