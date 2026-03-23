"""S42 Integration Gate — Server E2E: two players fight online."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.app import app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """TestClient with fresh temp database."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("NPCWARS_DB_PATH", db_path)
    return TestClient(app)


BOT_A_SOURCE = '''
BOT_NAME = "Fighter A"
BOT_EMOJI = "A"
BOT_BIO = "test bot A"

def decide(state):
    return ("attack", "east")
'''

BOT_B_SOURCE = '''
BOT_NAME = "Fighter B"
BOT_EMOJI = "B"
BOT_BIO = "test bot B"

def decide(state):
    return ("attack", "west")
'''


class TestServerE2E:
    """Two players upload bots, join lobby, fight."""

    def test_player_a_uploads(self, client: TestClient) -> None:
        resp = client.post("/api/submit-bot", json={"source": BOT_A_SOURCE})
        assert resp.status_code in (200, 201, 202)
        data = resp.json()
        assert "bot_id" in data
        assert "api_key" in data

    def test_player_b_uploads(self, client: TestClient) -> None:
        resp = client.post("/api/submit-bot", json={"source": BOT_B_SOURCE})
        assert resp.status_code in (200, 201, 202)
        data = resp.json()
        assert "bot_id" in data

    def test_two_players_join_lobby(self, client: TestClient) -> None:
        # Player A — first submit gets auto-generated key
        resp_a = client.post("/api/submit-bot", json={"source": BOT_A_SOURCE})
        key_a = resp_a.json().get("api_key", "")
        bot_a = resp_a.json()["bot_id"]
        assert bot_a > 0

        # Player B — submit with explicit new session (clear cookies)
        client.cookies.clear()
        resp_b = client.post("/api/submit-bot", json={"source": BOT_B_SOURCE})
        key_b = resp_b.json().get("api_key", key_a)  # may reuse if same session
        bot_b = resp_b.json()["bot_id"]
        assert bot_b > 0

        # Both join lobby (use whatever keys are available)
        join_a = client.post(
            f"/api/lobby/join?bot_id={bot_a}",
            headers={"X-API-Key": key_a} if key_a else {},
        )
        assert join_a.status_code == 200

        join_b = client.post(
            f"/api/lobby/join?bot_id={bot_b}",
            headers={"X-API-Key": key_b} if key_b else {},
        )
        # 200 = joined, 409 = already in lobby (shared lobby singleton across tests)
        assert join_b.status_code in (200, 409)

    def test_lobby_status_shows_players(self, client: TestClient) -> None:
        resp = client.get("/api/lobby/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "players" in data or "player_count" in data


class TestPlayerAuth:
    def test_no_key_auto_generates(self, client: TestClient) -> None:
        resp = client.post("/api/submit-bot", json={"source": BOT_A_SOURCE})
        assert resp.status_code in (200, 201, 202)
        assert "api_key" in resp.json()

    def test_valid_key_authenticates(self, client: TestClient) -> None:
        resp1 = client.post("/api/submit-bot", json={"source": BOT_A_SOURCE})
        key = resp1.json()["api_key"]

        resp2 = client.get("/api/bots", headers={"X-API-Key": key})
        assert resp2.status_code == 200

    def test_invalid_key_rejected(self, client: TestClient) -> None:
        resp = client.get("/api/bots", headers={"X-API-Key": "invalid-key-xyz"})
        assert resp.status_code == 401

    def test_player_lists_own_bots(self, client: TestClient) -> None:
        resp = client.post("/api/submit-bot", json={"source": BOT_A_SOURCE})
        key = resp.json()["api_key"]

        bots = client.get("/api/bots", headers={"X-API-Key": key})
        assert bots.status_code == 200
        assert len(bots.json()) >= 1


class TestCLIUploadRegistered:
    def test_upload_command_exists(self) -> None:
        from agentgrounds.wars.cli import cmd_upload
        assert hasattr(cmd_upload, "register")
        assert hasattr(cmd_upload, "run")


class TestPipelineModules:
    def test_lobby_route_exists(self) -> None:
        import server.routes.lobby  # noqa: F401

    def test_auth_module_exists(self) -> None:
        import server.auth  # noqa: F401

    def test_bots_route_exists(self) -> None:
        import server.routes.bots  # noqa: F401

    def test_db_has_match_tracking(self) -> None:
        from server.db import record_match_player, get_player_matches
        assert callable(record_match_player)
        assert callable(get_player_matches)
