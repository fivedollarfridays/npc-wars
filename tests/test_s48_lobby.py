"""Tests for T48.2 — enhanced lobby status API with player_list, status, match_id."""

from __future__ import annotations

from unittest.mock import patch

from server.lobby import Lobby, LOBBY_TIMEOUT, MAX_PLAYERS


def _make_bot(name: str = "TestBot", emoji: str = "T") -> dict:
    return {"name": name, "emoji": emoji, "source": "code", "player_id": "p1", "bot_id": 1}


# --- Cycle 1: player_list in status response ---


def test_status_includes_player_list():
    lobby = Lobby()
    lobby.join(_make_bot("Alpha", "A"))
    s = lobby.status()
    assert "player_list" in s
    assert isinstance(s["player_list"], list)
    assert len(s["player_list"]) == 1


def test_player_list_has_emoji_and_name():
    lobby = Lobby()
    lobby.join(_make_bot("Alpha", "A"))
    lobby.join(_make_bot("Bravo", "B"))
    s = lobby.status()
    assert s["player_list"][0] == {"emoji": "A", "name": "Alpha"}
    assert s["player_list"][1] == {"emoji": "B", "name": "Bravo"}


def test_player_list_empty_lobby():
    lobby = Lobby()
    s = lobby.status()
    assert s["player_list"] == []


# --- Cycle 2: status field ---


def test_status_waiting_when_empty():
    lobby = Lobby()
    assert lobby.status()["status"] == "waiting"


def test_status_filling_when_players_joined():
    lobby = Lobby()
    lobby.join(_make_bot("Alpha"))
    assert lobby.status()["status"] == "filling"


def test_status_running_after_trigger():
    """After match triggers, status should be 'running' (match_id is set)."""
    from server.queue import InMemoryQueue, set_backend

    set_backend(InMemoryQueue())
    lobby = Lobby()
    for i in range(MAX_PLAYERS):
        lobby.join(_make_bot(f"Bot{i}", "X"))
    assert lobby.status()["status"] == "running"


# --- Cycle 3: match_id tracking ---


def test_match_id_null_when_no_match():
    lobby = Lobby()
    assert lobby.status()["match_id"] is None


def test_match_id_set_after_trigger():
    from server.queue import InMemoryQueue, set_backend

    set_backend(InMemoryQueue())
    lobby = Lobby()
    for i in range(MAX_PLAYERS):
        lobby.join(_make_bot(f"Bot{i}", "X"))
    assert lobby.status()["match_id"] is not None
    assert isinstance(lobby.status()["match_id"], str)


def test_match_id_null_after_reset():
    from server.queue import InMemoryQueue, set_backend

    set_backend(InMemoryQueue())
    lobby = Lobby()
    for i in range(MAX_PLAYERS):
        lobby.join(_make_bot(f"Bot{i}", "X"))
    lobby.reset()
    assert lobby.status()["match_id"] is None


def test_timer_check_sets_match_id():
    """Poll-driven timer check should populate match_id on trigger."""
    from server.queue import InMemoryQueue, set_backend

    set_backend(InMemoryQueue())
    lobby = Lobby()
    lobby.join(_make_bot("A"))
    lobby.join(_make_bot("B"))
    with (
        patch("server.lobby.time.monotonic") as mock_time,
        patch("server.lobby._get_fill_bots", return_value=[_make_bot("AI1"), _make_bot("AI2")]),
    ):
        lobby._start_time = 100.0
        mock_time.return_value = 100.0 + LOBBY_TIMEOUT + 1.0
        lobby.check_timer()
    assert lobby.status()["match_id"] is not None


# --- Cycle 4: HTTP route calls check_timer on GET /status ---


def test_status_endpoint_calls_check_timer():
    """GET /api/lobby/status should call lobby.check_timer() for poll-driven triggers."""
    from fastapi.testclient import TestClient
    from server.app import app

    with patch("server.routes.lobby.get_lobby") as mock_get:
        mock_lobby = Lobby()
        mock_lobby.check_timer = patch.object(mock_lobby, "check_timer", wraps=mock_lobby.check_timer).start()
        mock_get.return_value = mock_lobby
        client = TestClient(app)
        client.get("/api/lobby/status")
        mock_lobby.check_timer.assert_called_once()
