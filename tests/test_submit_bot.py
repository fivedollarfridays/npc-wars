"""Tests for POST /api/submit-bot endpoint."""

import uuid

from fastapi.testclient import TestClient

from server.app import app
from server.routes.submit import clear_rate_limits

client = TestClient(app)

CLEAN_SOURCE = """\
def decide(me, enemies, storm):
    if enemies:
        return {"move": "north", "action": "shoot north"}
    return {"move": "south", "action": "none"}
"""


def setup_function():
    """Clear rate limits before each test."""
    clear_rate_limits()


def test_submit_valid_bot():
    """Clean source returns 202 with job_id."""
    response = client.post("/api/submit-bot", json={"source": CLEAN_SOURCE})
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data


def test_response_has_job_id_uuid():
    """job_id is a valid UUID4 string."""
    response = client.post("/api/submit-bot", json={"source": CLEAN_SOURCE})
    job_id = response.json()["job_id"]
    parsed = uuid.UUID(job_id, version=4)
    assert str(parsed) == job_id


def test_submit_invalid_bot():
    """Source with blocked import returns 400 with detail list."""
    bad_source = "import os\ndef decide(me, enemies, storm): pass\n"
    response = client.post("/api/submit-bot", json={"source": bad_source})
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert len(data["detail"]) >= 1
    assert any("os" in err for err in data["detail"])


def test_submit_empty_source():
    """Empty string source returns 400 with detail."""
    response = client.post("/api/submit-bot", json={"source": ""})
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_submit_missing_source():
    """Missing source field returns 422 (validation error)."""
    response = client.post("/api/submit-bot", json={})
    assert response.status_code == 422


def test_rate_limit():
    """Second request within 30s returns 429."""
    # First request should succeed
    r1 = client.post("/api/submit-bot", json={"source": CLEAN_SOURCE})
    assert r1.status_code == 202

    # Second request immediately should be rate limited
    r2 = client.post("/api/submit-bot", json={"source": CLEAN_SOURCE})
    assert r2.status_code == 429
