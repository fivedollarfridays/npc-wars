"""Tests for rival API endpoints and rival injection into lobby matches."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.db import create_api_key, create_player, init_db, store_bot
from server.rival_db import WINS_TO_ADVANCE, ensure_rival_progress, record_rival_attempt
from server.routes.lobby import reset_lobby
from server.routes.submit import clear_rate_limits

VALID_BOT_SOURCE = (
    'BOT_NAME = "TestBot"\n'
    'BOT_EMOJI = "\U0001f916"\n'
    'BOT_BIO = "A test bot"\n'
    "def decide(state):\n"
    '    return "north"\n'
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def _fresh_db():
    old_db = getattr(app.state, "db", None)
    app.state.db = init_db(":memory:")
    clear_rate_limits()
    reset_lobby()
    yield
    app.state.db = old_db


def _create_player_with_bot(
    player_id: str = "p1", bot_name: str = "TestBot"
) -> tuple[str, int]:
    conn = app.state.db
    create_player(conn, player_id, f"Player {player_id}")
    key = create_api_key(conn, player_id)
    bot_id = store_bot(
        conn, player_id, bot_name, "\U0001f916", VALID_BOT_SOURCE
    )
    return key, bot_id


# --- Rival status endpoint ---


class TestRivalStatusEndpoint:
    """GET /api/rival/status tests."""

    def test_returns_200(self) -> None:
        key, _ = _create_player_with_bot()
        resp = client.get("/api/rival/status", headers={"X-API-Key": key})
        assert resp.status_code == 200

    def test_default_tier(self) -> None:
        key, _ = _create_player_with_bot()
        resp = client.get("/api/rival/status", headers={"X-API-Key": key})
        data = resp.json()
        assert data["current_tier"] == 1
        assert data["attempts"] == 0

    def test_requires_auth(self) -> None:
        resp = client.get("/api/rival/status")
        assert resp.status_code == 401

    def test_rejects_invalid_key(self) -> None:
        resp = client.get(
            "/api/rival/status", headers={"X-API-Key": "bad-key"}
        )
        assert resp.status_code == 401


# --- Rival challenge endpoint ---


class TestRivalChallengeEndpoint:
    """POST /api/rival/challenge tests."""

    def test_returns_200_for_graduated(self) -> None:
        key, _ = _create_player_with_bot()
        conn = app.state.db
        ensure_rival_progress(conn, "p1")
        for _ in range(WINS_TO_ADVANCE * 5):
            record_rival_attempt(conn, "p1", won=True)
        resp = client.post(
            "/api/rival/challenge",
            json={"tier": 1},
            headers={"X-API-Key": key},
        )
        assert resp.status_code == 200

    def test_returns_queued_status(self) -> None:
        key, _ = _create_player_with_bot()
        conn = app.state.db
        ensure_rival_progress(conn, "p1")
        for _ in range(WINS_TO_ADVANCE * 5):
            record_rival_attempt(conn, "p1", won=True)
        resp = client.post(
            "/api/rival/challenge",
            json={"tier": 1},
            headers={"X-API-Key": key},
        )
        data = resp.json()
        assert data["status"] == "queued"

    def test_requires_auth(self) -> None:
        resp = client.post("/api/rival/challenge", json={"tier": 1})
        assert resp.status_code == 401


# --- Rival injection into lobby ---


class TestRivalInjection:
    """Rival bots replace one fill bot when player has uncleared tier."""

    def test_fill_bots_include_rival(self) -> None:
        """When a human joins, fill bots should include one rival."""
        from server.lobby import Lobby

        lobby = Lobby()
        key, bot_id = _create_player_with_bot()
        bot_config = {
            "name": "TestBot",
            "emoji": "\U0001f916",
            "source": VALID_BOT_SOURCE,
            "player_id": "p1",
            "bot_id": bot_id,
        }
        lobby.join(bot_config)
        # Force trigger by calling check_timer after setting start_time far in past
        lobby._start_time = 0.0
        with pytest.MonkeyPatch.context() as mp:
            triggered_configs: list = []

            def fake_enqueue(job: dict) -> None:
                triggered_configs.extend(job["bot_configs"])

            mp.setattr("server.lobby.enqueue_match", fake_enqueue)
            mp.setattr("server.lobby.queue_depth", lambda: 0)
            lobby.check_timer(conn=app.state.db)

        rival_bots = [c for c in triggered_configs if c.get("is_rival")]
        assert len(rival_bots) == 1
        assert rival_bots[0]["rival_tier"] == 1

    def test_fill_count_unchanged_with_rival(self) -> None:
        """Total bot count stays the same even with rival injection."""
        from server.lobby import Lobby, MIN_HUMANS_FOR_NO_FILL

        lobby = Lobby()
        key, bot_id = _create_player_with_bot()
        bot_config = {
            "name": "TestBot",
            "emoji": "\U0001f916",
            "source": VALID_BOT_SOURCE,
            "player_id": "p1",
            "bot_id": bot_id,
        }
        lobby.join(bot_config)
        lobby._start_time = 0.0

        with pytest.MonkeyPatch.context() as mp:
            triggered_configs: list = []

            def fake_enqueue(job: dict) -> None:
                triggered_configs.extend(job["bot_configs"])

            mp.setattr("server.lobby.enqueue_match", fake_enqueue)
            mp.setattr("server.lobby.queue_depth", lambda: 0)
            lobby.check_timer(conn=app.state.db)

        assert len(triggered_configs) == MIN_HUMANS_FOR_NO_FILL

    def test_no_rival_when_all_tiers_cleared(self) -> None:
        """No rival injected when player has cleared max tier."""
        from server.rival_db import MAX_RIVAL_TIER, ensure_rival_progress

        conn = app.state.db

        from server.lobby import Lobby

        key, bot_id = _create_player_with_bot("p2")
        # Create progress for p2 at max tier with enough wins
        ensure_rival_progress(conn, "p2")
        conn.execute(
            "UPDATE rival_progress SET current_tier = ?, wins = 99 "
            "WHERE player_id = ?",
            (MAX_RIVAL_TIER, "p2"),
        )
        conn.commit()

        lobby = Lobby()
        bot_config = {
            "name": "TestBot",
            "emoji": "\U0001f916",
            "source": VALID_BOT_SOURCE,
            "player_id": "p2",
            "bot_id": bot_id,
        }
        lobby.join(bot_config)
        lobby._start_time = 0.0

        with pytest.MonkeyPatch.context() as mp:
            triggered_configs: list = []

            def fake_enqueue(job: dict) -> None:
                triggered_configs.extend(job["bot_configs"])

            mp.setattr("server.lobby.enqueue_match", fake_enqueue)
            mp.setattr("server.lobby.queue_depth", lambda: 0)
            lobby.check_timer(conn=conn)

        rival_bots = [c for c in triggered_configs if c.get("is_rival")]
        assert len(rival_bots) == 0
