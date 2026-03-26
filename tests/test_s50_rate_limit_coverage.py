"""Tests for S50: rate limiting on mutating endpoints (tournament + lobby)."""

from __future__ import annotations

import os
import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.db import create_api_key, create_player, init_db, store_bot
from server.middleware.rate_limit import clear_all_rate_limit_state
from server.routes.lobby import reset_lobby


@pytest.fixture(autouse=True)
def _clean_state():
    """Reset all rate-limit stores and env before each test."""
    os.environ["NPCWARS_SECURE_COOKIES"] = "0"
    clear_all_rate_limit_state()
    reset_lobby()


def _client() -> TestClient:
    """Create a test client with fresh in-memory DB."""
    app.state.db = init_db(":memory:")
    return TestClient(app)


def _make_player(conn, pid: str = "p1") -> tuple[str, int]:
    """Create player + API key + bot. Returns (api_key, bot_id)."""
    create_player(conn, pid, f"Player {pid}")
    key = create_api_key(conn, pid)
    bot_id = store_bot(
        conn, pid, f"Bot {pid}", "B",
        "BOT_NAME='T'\ndef setup(s): pass\ndef take_turn(s): return 'north'",
    )
    return key, bot_id


# ── Tournament create rate limit ─────────────────────────────────


def test_tournament_create_rate_limited() -> None:
    """6th tournament create within 60s should return 429."""
    client = _client()
    conn = app.state.db
    key, _ = _make_player(conn, "rl1")

    for i in range(5):
        resp = client.post(
            "/api/tournament/create",
            params={"name": f"Cup{i}", "size": 8},
            headers={"X-API-Key": key},
        )
        assert resp.status_code == 200, f"Request {i+1} should succeed"

    resp = client.post(
        "/api/tournament/create",
        params={"name": "Cup5", "size": 8},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 429
    assert "retry-after" in resp.headers


# ── Lobby join rate limit ────────────────────────────────────────


@patch("server.lobby.Lobby._trigger_match")
def test_lobby_join_rate_limited(_mock_trigger: object) -> None:
    """11th lobby join within 60s from same client should return 429."""
    client = _client()
    conn = app.state.db
    key, bot_id = _make_player(conn, "lrl0")

    for i in range(11):
        resp = client.post(
            "/api/lobby/join",
            params={"bot_id": bot_id},
            headers={"X-API-Key": key},
        )
        if i < 10:
            # May be 200 or 409 (lobby full/duplicate), but NOT 429
            assert resp.status_code != 429, f"Request {i+1} should not be rate limited"
        else:
            assert resp.status_code == 429


# ── Bucket independence ──────────────────────────────────────────


def test_rate_limit_buckets_independent() -> None:
    """Submitting a bot should not consume tournament rate limit."""
    client = _client()
    conn = app.state.db
    key, bot_id = _make_player(conn, "ind1")

    clean_source = (
        "def decide(me, enemies, storm):\n"
        "    return {'move': 'north', 'action': 'none'}\n"
    )
    # Submit bot (uses the old submit rate limit bucket)
    client.post("/api/submit-bot", json={"source": clean_source})

    # Tournament create should still work (separate bucket)
    resp = client.post(
        "/api/tournament/create",
        params={"name": "Ind", "size": 8},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200


# ── Window reset ─────────────────────────────────────────────────


def test_tournament_rate_limit_resets() -> None:
    """After 60s window expires, tournament create should succeed again."""
    client = _client()
    conn = app.state.db
    key, _ = _make_player(conn, "rst1")

    # Exhaust the limit
    for i in range(5):
        client.post(
            "/api/tournament/create",
            params={"name": f"R{i}", "size": 8},
            headers={"X-API-Key": key},
        )

    # 6th should fail
    resp = client.post(
        "/api/tournament/create",
        params={"name": "R5", "size": 8},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 429

    # Advance time past the 60s window
    with patch("server.middleware.rate_limit.time") as mock_time:
        future = time.monotonic() + 61
        mock_time.monotonic.return_value = future
        resp = client.post(
            "/api/tournament/create",
            params={"name": "R6", "size": 8},
            headers={"X-API-Key": key},
        )
        assert resp.status_code == 200
