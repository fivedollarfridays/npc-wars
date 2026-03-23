"""Tests for lobby HTTP endpoints and matchmaking pipeline."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from server.app import app
from unittest.mock import patch

from server.db import (
    create_api_key,
    create_player,
    get_player_matches,
    init_db,
    record_match_player,
    store_bot,
)
from server.lobby import MAX_PLAYERS
from server.routes.lobby import reset_lobby
from server.routes.submit import clear_rate_limits


# ── Fixtures ────────────────────────────────────────────────────────

VALID_BOT_SOURCE = (
    'BOT_NAME = "LobbyBot"\n'
    'BOT_EMOJI = "L"\n'
    'BOT_BIO = "A test bot"\n'
    "def decide(state):\n"
    '    return "north"\n'
)


@pytest.fixture(autouse=True)
def _clear_rates():
    clear_rate_limits()
    reset_lobby()


@pytest.fixture()
def db(tmp_path):
    """Fresh DB connection with all tables."""
    return init_db(str(tmp_path / "test.db"))


@pytest.fixture()
def client(tmp_path):
    """TestClient with fresh DB and results dir."""
    conn = init_db(str(tmp_path / "lobby_test.db"))
    old_db = app.state.db
    old_results = getattr(app.state, "results_dir", "results")
    rdir = tmp_path / "results"
    rdir.mkdir()
    app.state.db = conn
    app.state.results_dir = str(rdir)
    yield TestClient(app)
    app.state.db = old_db
    app.state.results_dir = old_results


def _make_player_with_bot(conn, player_name: str = "alice") -> tuple[str, str, int]:
    """Create a player with an API key and a bot. Returns (player_id, api_key, bot_id)."""
    player_id = f"pid_{player_name}"
    create_player(conn, player_id, player_name)
    api_key = create_api_key(conn, player_id)
    bot_id = store_bot(conn, player_id, f"{player_name}_bot", "T", VALID_BOT_SOURCE)
    return player_id, api_key, bot_id


# ── Cycle 1: DB match tracking ─────────────────────────────────────


def test_record_match_player(db):
    """record_match_player stores a match-player-bot association."""
    create_player(db, "p1", "Alice")
    bot_id = store_bot(db, "p1", "Bot1", "B", "source")
    record_match_player(db, match_id=1, player_id="p1", bot_id=bot_id)
    matches = get_player_matches(db, "p1")
    assert matches == [1]


def test_get_player_matches_returns_recent_first(db):
    """get_player_matches returns match IDs in descending order."""
    create_player(db, "p1", "Alice")
    bot_id = store_bot(db, "p1", "Bot1", "B", "source")
    for mid in [1, 2, 3]:
        record_match_player(db, match_id=mid, player_id="p1", bot_id=bot_id)
    matches = get_player_matches(db, "p1")
    assert matches == [3, 2, 1]


def test_get_player_matches_respects_limit(db):
    """get_player_matches respects the limit parameter."""
    create_player(db, "p1", "Alice")
    bot_id = store_bot(db, "p1", "Bot1", "B", "source")
    for mid in range(1, 6):
        record_match_player(db, match_id=mid, player_id="p1", bot_id=bot_id)
    matches = get_player_matches(db, "p1", limit=2)
    assert matches == [5, 4]


# ── Cycle 2: POST /api/lobby/join ──────────────────────────────────


def test_join_lobby_valid_bot(client):
    """POST /api/lobby/join with a valid bot_id returns 200."""
    conn = app.state.db
    _pid, api_key, bot_id = _make_player_with_bot(conn, "alice")
    resp = client.post(
        f"/api/lobby/join?bot_id={bot_id}",
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["joined"] is True
    assert data["lobby"]["players"] >= 1


def test_join_lobby_invalid_bot(client):
    """POST /api/lobby/join with nonexistent bot_id returns 404."""
    conn = app.state.db
    _pid, api_key, _bid = _make_player_with_bot(conn, "bob")
    resp = client.post(
        "/api/lobby/join?bot_id=9999",
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 404


def test_join_lobby_wrong_owner(client):
    """POST /api/lobby/join with another player's bot returns 404."""
    conn = app.state.db
    _pid1, _key1, bot_id = _make_player_with_bot(conn, "alice")
    _pid2, key2, _bid2 = _make_player_with_bot(conn, "bob")
    resp = client.post(
        f"/api/lobby/join?bot_id={bot_id}",
        headers={"X-API-Key": key2},
    )
    assert resp.status_code == 404


# ── Cycle 3: GET /api/lobby/status ─────────────────────────────────


def test_lobby_status_empty(client):
    """GET /api/lobby/status returns empty lobby state."""
    resp = client.get("/api/lobby/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["players"] == 0
    assert data["triggered"] is False


# ── Cycle 4: GET /api/lobby/history ────────────────────────────────


def test_lobby_history_returns_matches(client):
    """GET /api/lobby/history returns match IDs for the player."""
    conn = app.state.db
    pid, api_key, bot_id = _make_player_with_bot(conn, "alice")
    record_match_player(conn, match_id=42, player_id=pid, bot_id=bot_id)
    record_match_player(conn, match_id=43, player_id=pid, bot_id=bot_id)
    resp = client.get(
        "/api/lobby/history",
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 200
    assert resp.json()["matches"] == [43, 42]


def test_lobby_history_empty(client):
    """GET /api/lobby/history returns empty list for new player."""
    conn = app.state.db
    _pid, api_key, _bid = _make_player_with_bot(conn, "newbie")
    resp = client.get(
        "/api/lobby/history",
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 200
    assert resp.json()["matches"] == []


# ── Cycle 5: Pipeline — lobby fill triggers match enqueue ──────────


def test_full_lobby_triggers_enqueue(client):
    """When MAX_PLAYERS join, the lobby enqueues a match job."""
    conn = app.state.db
    with (
        patch("server.lobby.enqueue_match") as mock_enqueue,
        patch("server.lobby.queue_depth", return_value=0),
    ):
        for i in range(MAX_PLAYERS):
            _pid, api_key, bot_id = _make_player_with_bot(conn, f"player{i}")
            resp = client.post(
                f"/api/lobby/join?bot_id={bot_id}",
                headers={"X-API-Key": api_key},
            )
            assert resp.status_code == 200
        mock_enqueue.assert_called_once()
        job = mock_enqueue.call_args[0][0]
        assert len(job["bot_configs"]) == MAX_PLAYERS


def test_lobby_full_rejects_extra(client):
    """After MAX_PLAYERS join, additional joins are rejected with 409."""
    conn = app.state.db
    with (
        patch("server.lobby.enqueue_match"),
        patch("server.lobby.queue_depth", return_value=0),
    ):
        for i in range(MAX_PLAYERS):
            _pid, api_key, bot_id = _make_player_with_bot(conn, f"p{i}")
            client.post(
                f"/api/lobby/join?bot_id={bot_id}",
                headers={"X-API-Key": api_key},
            )
        # Extra player should be rejected
        _pid, api_key, bot_id = _make_player_with_bot(conn, "extra")
        resp = client.post(
            f"/api/lobby/join?bot_id={bot_id}",
            headers={"X-API-Key": api_key},
        )
        assert resp.status_code == 409
