"""Tests for API key auth + bot persistence routes (T42.1)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.routes.submit import clear_rate_limits


@pytest.fixture(autouse=True)
def _clear():
    clear_rate_limits()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


VALID_SOURCE = (
    'BOT_NAME = "TestAuth"\n'
    'BOT_EMOJI = "T"\n'
    "def decide(state):\n"
    '    return ("rest",)\n'
)


# ── 1. Submit with auth ──────────────────────────────────────────────


class TestSubmitAuth:
    """POST /api/submit-bot with API key authentication."""

    def test_submit_without_key_auto_generates(self, client: TestClient):
        """First submit without key returns api_key + bot_id."""
        resp = client.post("/api/submit-bot", json={"source": VALID_SOURCE})
        assert resp.status_code == 202
        data = resp.json()
        assert "api_key" in data
        assert "bot_id" in data
        assert isinstance(data["bot_id"], int)

    def test_submit_with_valid_key(self, client: TestClient):
        """Submit with valid API key authenticates and stores bot."""
        # First request to get a key
        r1 = client.post("/api/submit-bot", json={"source": VALID_SOURCE})
        key = r1.json()["api_key"]

        clear_rate_limits()

        # Second request with key should authenticate
        r2 = client.post(
            "/api/submit-bot",
            json={"source": VALID_SOURCE},
            headers={"X-API-Key": key},
        )
        assert r2.status_code == 202
        data = r2.json()
        assert "bot_id" in data
        # Should NOT return api_key again for existing users
        assert "api_key" not in data

    def test_submit_with_invalid_key_returns_401(self, client: TestClient):
        """Invalid API key returns 401."""
        resp = client.post(
            "/api/submit-bot",
            json={"source": VALID_SOURCE},
            headers={"X-API-Key": "bad-key-does-not-exist"},
        )
        assert resp.status_code == 401
        assert "Invalid API key" in resp.json()["detail"]


# ── 2. Bot list routes ───────────────────────────────────────────────


class TestBotRoutes:
    """GET /api/bots and GET /api/bots/{id}."""

    def _submit_and_get_key(self, client: TestClient) -> tuple[str, int]:
        """Helper: submit a bot, return (api_key, bot_id)."""
        resp = client.post("/api/submit-bot", json={"source": VALID_SOURCE})
        data = resp.json()
        return data["api_key"], data["bot_id"]

    def test_list_bots_requires_auth(self, client: TestClient):
        resp = client.get("/api/bots")
        assert resp.status_code == 401

    def test_list_bots_with_key(self, client: TestClient):
        key, bot_id = self._submit_and_get_key(client)
        resp = client.get("/api/bots", headers={"X-API-Key": key})
        assert resp.status_code == 200
        bots = resp.json()
        assert len(bots) >= 1
        assert any(b["id"] == bot_id for b in bots)

    def test_get_bot_detail(self, client: TestClient):
        key, bot_id = self._submit_and_get_key(client)
        resp = client.get(f"/api/bots/{bot_id}", headers={"X-API-Key": key})
        assert resp.status_code == 200
        bot = resp.json()
        assert bot["id"] == bot_id
        assert bot["name"] == "TestAuth"
        assert bot["emoji"] == "T"
        assert "source" in bot

    def test_get_bot_not_found(self, client: TestClient):
        key, _ = self._submit_and_get_key(client)
        resp = client.get("/api/bots/9999", headers={"X-API-Key": key})
        assert resp.status_code == 404

    def test_bots_isolated_between_players(self, client: TestClient):
        """Two different API keys see separate bot lists."""
        key1, _ = self._submit_and_get_key(client)
        clear_rate_limits()
        key2, _ = self._submit_and_get_key(client)

        assert key1 != key2

        bots1 = client.get("/api/bots", headers={"X-API-Key": key1}).json()
        bots2 = client.get("/api/bots", headers={"X-API-Key": key2}).json()

        ids1 = {b["id"] for b in bots1}
        ids2 = {b["id"] for b in bots2}
        assert ids1.isdisjoint(ids2)
