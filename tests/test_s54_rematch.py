"""Tests for T54.5: Rematch any tier after graduation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.db import create_api_key, create_player, init_db, store_bot
from server.rival_db import WINS_TO_ADVANCE, ensure_rival_progress, record_rival_attempt


@pytest.fixture(autouse=True)
def setup_db():
    old_db = getattr(app.state, "db", None)
    app.state.db = init_db(":memory:")
    yield
    app.state.db = old_db


client = TestClient(app)


def _create_player(player_id: str = "p1") -> str:
    conn = app.state.db
    create_player(conn, player_id, "Test")
    key = create_api_key(conn, player_id)
    store_bot(conn, player_id, "Bot", "\U0001f916", "def decide(s): return ('rest',)")
    return key


def _graduate_player(player_id: str = "p1") -> None:
    conn = app.state.db
    ensure_rival_progress(conn, player_id)
    for _ in range(WINS_TO_ADVANCE * 5):
        record_rival_attempt(conn, player_id, won=True)


class TestChallengeEndpoint:
    def test_challenge_accepts_tier(self):
        key = _create_player()
        _graduate_player()
        resp = client.post(
            "/api/rival/challenge", json={"tier": 3}, headers={"X-API-Key": key}
        )
        assert resp.status_code == 200
        assert resp.json()["tier"] == 3

    def test_challenge_rejects_non_graduated(self):
        key = _create_player()
        resp = client.post(
            "/api/rival/challenge", json={"tier": 3}, headers={"X-API-Key": key}
        )
        assert resp.status_code == 403

    def test_challenge_rejects_invalid_tier_low(self):
        key = _create_player()
        _graduate_player()
        resp = client.post(
            "/api/rival/challenge", json={"tier": 0}, headers={"X-API-Key": key}
        )
        assert resp.status_code in (400, 422)

    def test_challenge_rejects_invalid_tier_high(self):
        key = _create_player()
        _graduate_player()
        resp = client.post(
            "/api/rival/challenge", json={"tier": 6}, headers={"X-API-Key": key}
        )
        assert resp.status_code in (400, 422)

    def test_challenge_requires_auth(self):
        resp = client.post("/api/rival/challenge", json={"tier": 1})
        assert resp.status_code == 401

    def test_challenge_valid_tiers(self):
        key = _create_player()
        _graduate_player()
        for tier in range(1, 6):
            resp = client.post(
                "/api/rival/challenge",
                json={"tier": tier},
                headers={"X-API-Key": key},
            )
            assert resp.status_code == 200, f"Tier {tier} failed"

    def test_challenge_returns_status(self):
        key = _create_player()
        _graduate_player()
        resp = client.post(
            "/api/rival/challenge", json={"tier": 2}, headers={"X-API-Key": key}
        )
        data = resp.json()
        assert data["status"] == "queued"
        assert data["tier"] == 2
