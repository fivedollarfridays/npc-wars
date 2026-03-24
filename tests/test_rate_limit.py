"""Tests for session management and rate limiting middleware."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from server.app import app
from server.middleware.rate_limit import clear_rate_limit_state
from server.routes.submit import clear_rate_limits

CLEAN_SOURCE = """\
BOT_NAME = "TestBot"
BOT_EMOJI = "T"

def decide(state):
    return ("rest",)
"""


def _make_client() -> TestClient:
    return TestClient(app)


def setup_function():
    """Reset state before each test."""
    clear_rate_limit_state()
    clear_rate_limits()


# --- Session tests ---


def test_first_request_gets_session_cookie():
    """First request to any endpoint should receive a session cookie."""
    client = _make_client()
    response = client.get("/health")
    assert "npcwars_session" in response.cookies


def test_session_cookie_persists():
    """Subsequent requests reuse the same session token."""
    client = _make_client()
    r1 = client.get("/health")
    token1 = r1.cookies.get("npcwars_session")

    r2 = client.get("/health")
    # TestClient sends cookies back automatically, so no new Set-Cookie
    # The session should be the same (no new cookie set)
    assert token1 is not None
    # Second response should NOT set a new cookie (already has one)
    assert "npcwars_session" not in r2.cookies


# --- Rate limit header tests ---


def test_rate_limit_headers_present():
    """Successful submit should include rate limit headers."""
    client = _make_client()
    response = client.post("/api/submit-bot", json={"source": CLEAN_SOURCE})
    assert response.status_code == 202
    assert "x-ratelimit-limit" in response.headers
    assert "x-ratelimit-remaining" in response.headers
    assert response.headers["x-ratelimit-limit"] == "1"


# --- Rate limit enforcement tests ---


def test_second_submission_within_window_returns_429():
    """Second submit within 30s window should be rate limited."""
    client = _make_client()
    r1 = client.post("/api/submit-bot", json={"source": CLEAN_SOURCE})
    assert r1.status_code == 202

    r2 = client.post("/api/submit-bot", json={"source": CLEAN_SOURCE})
    assert r2.status_code == 429


def test_429_has_retry_after_header():
    """429 response should include Retry-After header."""
    client = _make_client()
    client.post("/api/submit-bot", json={"source": CLEAN_SOURCE})
    r2 = client.post("/api/submit-bot", json={"source": CLEAN_SOURCE})
    assert r2.status_code == 429
    assert "retry-after" in r2.headers
    retry_after = int(r2.headers["retry-after"])
    assert 0 < retry_after <= 30


def test_submission_after_window_succeeds():
    """Submission after the rate limit window expires should succeed."""
    client = _make_client()
    client.post("/api/submit-bot", json={"source": CLEAN_SOURCE})

    # Advance time past the window
    with patch("server.middleware.rate_limit.time") as mock_time:
        # First call was at real time; now pretend 31 seconds passed
        import time as real_time

        future = real_time.monotonic() + 31
        mock_time.monotonic.return_value = future
        r2 = client.post("/api/submit-bot", json={"source": CLEAN_SOURCE})
        assert r2.status_code == 202
