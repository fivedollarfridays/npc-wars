"""Tests for tournament DB storage functions."""

from __future__ import annotations

import json
import sqlite3

from server.db import init_db
from server.tournament_db import (
    create_tournament,
    get_tournament,
    list_tournaments,
    update_tournament,
)


def _make_conn() -> sqlite3.Connection:
    """Create an in-memory DB with all tables."""
    return init_db(":memory:")


def test_create_tournament_returns_id() -> None:
    conn = _make_conn()
    tid = create_tournament(conn, "Test Cup", 8, "arena")
    assert isinstance(tid, int)
    assert tid >= 1


def test_get_tournament_returns_dict() -> None:
    conn = _make_conn()
    tid = create_tournament(conn, "Test Cup", 8, "arena")
    row = get_tournament(conn, tid)
    assert row is not None
    assert row["name"] == "Test Cup"
    assert row["size"] == 8
    assert row["status"] == "open"
    assert row["map_name"] == "arena"
    assert row["winner"] is None
    assert row["bracket_json"] == "{}"


def test_get_tournament_not_found() -> None:
    conn = _make_conn()
    assert get_tournament(conn, 999) is None


def test_update_tournament() -> None:
    conn = _make_conn()
    tid = create_tournament(conn, "Cup", 8, "arena")
    bracket = json.dumps({"name": "Cup", "size": 8, "players": ["a", "b"]})
    update_tournament(conn, tid, bracket, "running", None)
    row = get_tournament(conn, tid)
    assert row is not None
    assert row["bracket_json"] == bracket
    assert row["status"] == "running"


def test_update_tournament_with_winner() -> None:
    conn = _make_conn()
    tid = create_tournament(conn, "Cup", 8, "arena")
    update_tournament(conn, tid, "{}", "complete", "player_1")
    row = get_tournament(conn, tid)
    assert row is not None
    assert row["winner"] == "player_1"
    assert row["status"] == "complete"


def test_list_tournaments_empty() -> None:
    conn = _make_conn()
    result = list_tournaments(conn)
    assert result == []


def test_list_tournaments_returns_recent() -> None:
    conn = _make_conn()
    create_tournament(conn, "Cup A", 8, "arena")
    create_tournament(conn, "Cup B", 16, "arena")
    result = list_tournaments(conn)
    assert len(result) == 2
    # Most recent first
    assert result[0]["name"] == "Cup B"
    assert result[1]["name"] == "Cup A"


def test_list_tournaments_respects_limit() -> None:
    conn = _make_conn()
    for i in range(5):
        create_tournament(conn, f"Cup {i}", 8, "arena")
    result = list_tournaments(conn, limit=3)
    assert len(result) == 3
