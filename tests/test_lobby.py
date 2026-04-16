"""Tests for server.lobby — time-limited lobby with AI fill."""

from __future__ import annotations

from unittest.mock import patch

from conftest import NotInMemoryQueue
from server.lobby import Lobby, MAX_PLAYERS, MIN_HUMANS_FOR_NO_FILL, LOBBY_TIMEOUT
from server.queue import set_backend, dequeue_match


def _make_bot(name: str = "TestBot") -> dict:
    return {"name": name, "emoji": "T"}


def _queue() -> NotInMemoryQueue:
    q = NotInMemoryQueue()
    set_backend(q)
    return q


# --- Cycle 1: join behaviour ---


def test_join_adds_player():
    lobby = Lobby()
    result = lobby.join(_make_bot("A"))
    assert result is True
    assert lobby.status()["players"] == 1


def test_join_full_lobby_rejected():
    _queue()
    lobby = Lobby()
    for i in range(MAX_PLAYERS):
        lobby.join(_make_bot(f"Bot{i}"))
    result = lobby.join(_make_bot("Extra"))
    assert result is False


# --- Cycle 2: match triggering ---


def test_max_players_triggers_match():
    _queue()
    lobby = Lobby()
    for i in range(MAX_PLAYERS):
        lobby.join(_make_bot(f"Bot{i}"))
    assert lobby.status()["triggered"] is True
    job = dequeue_match(timeout=0)
    assert job is not None
    assert len(job["bot_configs"]) == MAX_PLAYERS


def test_timer_triggers_match():
    _queue()
    lobby = Lobby()
    lobby.join(_make_bot("A"))
    lobby.join(_make_bot("B"))
    # Simulate time passing beyond LOBBY_TIMEOUT
    with (
        patch("server.lobby.time.monotonic") as mock_time,
        patch("server.lobby._get_fill_bots", return_value=[_make_bot("AI1"), _make_bot("AI2")]),
    ):
        lobby._start_time = 100.0
        mock_time.return_value = 100.0 + LOBBY_TIMEOUT + 1.0
        result = lobby.check_timer()
    assert result is True
    assert lobby.status()["triggered"] is True
    job = dequeue_match(timeout=0)
    assert job is not None


def test_check_timer_no_trigger_before_timeout():
    lobby = Lobby()
    lobby.join(_make_bot("A"))
    with patch("server.lobby.time.monotonic", return_value=lobby._start_time + 10.0):
        result = lobby.check_timer()
    assert result is False
    assert lobby.status()["triggered"] is False


# --- Cycle 3: status and reset ---


def test_status_shows_time_remaining():
    lobby = Lobby()
    lobby.join(_make_bot("A"))
    with patch("server.lobby.time.monotonic", return_value=lobby._start_time + 10.0):
        s = lobby.status()
    assert s["players"] == 1
    assert s["max"] == MAX_PLAYERS
    assert s["time_remaining"] == 20.0
    assert s["triggered"] is False


def test_status_empty_lobby():
    lobby = Lobby()
    s = lobby.status()
    assert s["players"] == 0
    assert s["time_remaining"] is None
    assert s["triggered"] is False


def test_lobby_reset():
    _queue()
    lobby = Lobby()
    for i in range(MAX_PLAYERS):
        lobby.join(_make_bot(f"Bot{i}"))
    assert lobby.status()["triggered"] is True
    lobby.reset()
    s = lobby.status()
    assert s["players"] == 0
    assert s["time_remaining"] is None
    assert s["triggered"] is False


# --- Cycle 4: AI fill behaviour ---


def test_fill_bots_when_few_humans():
    """Fewer than MIN_HUMANS_FOR_NO_FILL humans triggers AI fill."""
    _queue()
    lobby = Lobby()
    lobby.join(_make_bot("H1"))
    lobby.join(_make_bot("H2"))
    fill = [_make_bot(f"AI{i}") for i in range(MIN_HUMANS_FOR_NO_FILL - 2)]
    with (
        patch("server.lobby.time.monotonic") as mock_time,
        patch("server.lobby._get_fill_bots", return_value=fill) as mock_fill,
    ):
        lobby._start_time = 100.0
        mock_time.return_value = 100.0 + LOBBY_TIMEOUT + 1.0
        lobby.check_timer()
    mock_fill.assert_called_once_with(MIN_HUMANS_FOR_NO_FILL - 2)
    job = dequeue_match(timeout=0)
    assert job is not None
    assert len(job["bot_configs"]) == MIN_HUMANS_FOR_NO_FILL


def test_no_fill_when_enough_humans():
    """4+ humans should NOT get AI fill bots."""
    _queue()
    lobby = Lobby()
    for i in range(MIN_HUMANS_FOR_NO_FILL):
        lobby.join(_make_bot(f"H{i}"))
    with (
        patch("server.lobby.time.monotonic") as mock_time,
        patch("server.lobby._get_fill_bots") as mock_fill,
    ):
        lobby._start_time = 100.0
        mock_time.return_value = 100.0 + LOBBY_TIMEOUT + 1.0
        lobby.check_timer()
    mock_fill.assert_not_called()
    job = dequeue_match(timeout=0)
    assert len(job["bot_configs"]) == MIN_HUMANS_FOR_NO_FILL
