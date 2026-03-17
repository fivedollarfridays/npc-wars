"""Tests for server.db — SQLite player registry."""

import pytest

from server.db import (
    create_player,
    create_session,
    expire_session,
    get_player,
    get_session,
    init_db,
    list_players,
)


@pytest.fixture()
def db(tmp_path):
    """Return an initialised in-memory-like DB connection via tmp_path."""
    db_path = str(tmp_path / "test.db")
    return init_db(db_path)


# ── init_db ──────────────────────────────────────────────────────────


def test_init_db_creates_tables(tmp_path):
    conn = init_db(str(tmp_path / "test.db"))
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "players" in tables
    assert "sessions" in tables
    conn.close()


def test_init_db_idempotent(tmp_path):
    path = str(tmp_path / "test.db")
    conn1 = init_db(path)
    conn1.close()
    # Second call must not raise
    conn2 = init_db(path)
    conn2.close()


# ── players CRUD ─────────────────────────────────────────────────────


def test_create_and_get_player(db):
    result = create_player(db, "p1", "Alice")
    assert result["id"] == "p1"
    assert result["name"] == "Alice"
    assert "created" in result

    fetched = get_player(db, "p1")
    assert fetched is not None
    assert fetched["id"] == "p1"
    assert fetched["name"] == "Alice"


def test_get_nonexistent_player_returns_none(db):
    assert get_player(db, "no-such-id") is None


def test_list_players_empty(db):
    assert list_players(db) == []


def test_list_players_returns_all(db):
    create_player(db, "p1", "Alice")
    create_player(db, "p2", "Bob")
    players = list_players(db)
    assert len(players) == 2
    names = {p["name"] for p in players}
    assert names == {"Alice", "Bob"}


# ── sessions ─────────────────────────────────────────────────────────


def test_create_and_get_session(db):
    create_player(db, "p1", "Alice")
    result = create_session(db, "tok1", "p1", "2099-01-01T00:00:00+00:00")
    assert result["token"] == "tok1"
    assert result["player_id"] == "p1"

    fetched = get_session(db, "tok1")
    assert fetched is not None
    assert fetched["token"] == "tok1"
    assert fetched["player_id"] == "p1"


def test_get_nonexistent_session_returns_none(db):
    assert get_session(db, "no-such-token") is None


def test_expire_session(db):
    create_player(db, "p1", "Alice")
    create_session(db, "tok1", "p1", "2099-01-01T00:00:00+00:00")
    assert expire_session(db, "tok1") is True
    assert get_session(db, "tok1") is None


def test_expire_nonexistent_session_returns_false(db):
    assert expire_session(db, "no-such-token") is False
