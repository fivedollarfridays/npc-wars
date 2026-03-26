"""Tests for security logging and submit error format (T50.6)."""

from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.db import create_api_key, create_player, init_db
from server.routes.submit import clear_rate_limits


@pytest.fixture(autouse=True)
def _setup_db():
    old_db = getattr(app.state, "db", None)
    app.state.db = init_db(":memory:")
    clear_rate_limits()
    yield
    app.state.db = old_db


client = TestClient(app)

MALICIOUS_SOURCE = "import os\nBOT_NAME='x'\nBOT_EMOJI='x'\ndef decide(s): return ('rest',)"
CLEAN_SOURCE = "BOT_NAME='ok'\nBOT_EMOJI='o'\ndef decide(s): return ('rest',)"


def _create_player_with_key() -> str:
    """Create a player and return their API key."""
    conn = app.state.db
    player = create_player(conn, "test-player-1", "tester")
    return create_api_key(conn, player["id"])


# --- Auth failure logging ---


def test_auth_failure_invalid_key_logs_warning(caplog: pytest.LogCaptureFixture) -> None:
    """Invalid API key triggers a warning log."""
    with caplog.at_level(logging.WARNING, logger="server.auth"):
        client.get("/api/bots", headers={"X-API-Key": "invalid-key-123"})
    assert any("Auth failure" in r.message for r in caplog.records)


def test_auth_failure_does_not_log_key_value(caplog: pytest.LogCaptureFixture) -> None:
    """The actual key value must never appear in logs."""
    with caplog.at_level(logging.WARNING, logger="server.auth"):
        client.get("/api/bots", headers={"X-API-Key": "secret-key-abc"})
    for record in caplog.records:
        assert "secret-key-abc" not in record.message


def test_auth_failure_missing_key_logs_warning(caplog: pytest.LogCaptureFixture) -> None:
    """Missing API key on a protected endpoint triggers a warning log."""
    with caplog.at_level(logging.WARNING, logger="server.auth"):
        client.get("/api/bots")
    assert any("Auth failure" in r.message for r in caplog.records)


# --- Scan violation logging ---


def test_scan_violation_logs_warning(caplog: pytest.LogCaptureFixture) -> None:
    """Submitting code with blocked imports triggers a warning log."""
    key = _create_player_with_key()
    with caplog.at_level(logging.WARNING, logger="server.routes.submit"):
        client.post(
            "/api/submit-bot",
            json={"source": MALICIOUS_SOURCE},
            headers={"X-API-Key": key},
        )
    assert any("scan violation" in r.message.lower() for r in caplog.records)


# --- Error format: detail instead of errors ---


def test_empty_source_returns_detail_format() -> None:
    """Empty source returns {'detail': ...} not {'errors': [...]}."""
    resp = client.post("/api/submit-bot", json={"source": ""})
    data = resp.json()
    assert resp.status_code == 400
    assert "detail" in data
    assert "errors" not in data


def test_scan_failure_returns_detail_format() -> None:
    """Scan violations return {'detail': ...} not {'errors': [...]}."""
    resp = client.post("/api/submit-bot", json={"source": MALICIOUS_SOURCE})
    data = resp.json()
    assert resp.status_code == 400
    assert "detail" in data
    assert "errors" not in data
