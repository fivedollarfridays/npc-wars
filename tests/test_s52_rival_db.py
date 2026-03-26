"""Tests for rival progress DB table and CRUD functions."""

import threading

import pytest

from server.db import _write_lock, init_db
from server.rival_db import (
    WINS_TO_ADVANCE,
    MAX_RIVAL_TIER,
    ensure_rival_progress,
    get_rival_progress,
    get_rival_tier,
    init_rival_table,
    record_rival_attempt,
)


@pytest.fixture
def conn():
    db = init_db(":memory:")
    init_rival_table(db)
    return db


def test_init_rival_table_idempotent(conn):
    init_rival_table(conn)  # second call should not error


def test_get_progress_unknown_player(conn):
    assert get_rival_progress(conn, "unknown") is None


def test_ensure_creates_default(conn):
    progress = ensure_rival_progress(conn, "player1")
    assert progress["current_tier"] == 1
    assert progress["attempts"] == 0
    assert progress["wins"] == 0


def test_ensure_idempotent(conn):
    p1 = ensure_rival_progress(conn, "player1")
    p2 = ensure_rival_progress(conn, "player1")
    assert p1["current_tier"] == p2["current_tier"]


def test_record_attempt_increments(conn):
    ensure_rival_progress(conn, "player1")
    result = record_rival_attempt(conn, "player1", won=False)
    assert result["attempts"] == 1
    assert result["wins"] == 0
    assert result["current_tier"] == 1


def test_record_win_advances_tier(conn):
    ensure_rival_progress(conn, "player1")
    # Need WINS_TO_ADVANCE wins to advance
    for _ in range(WINS_TO_ADVANCE - 1):
        record_rival_attempt(conn, "player1", won=True)
    result = record_rival_attempt(conn, "player1", won=True)
    assert result["wins"] == 0  # reset after advance
    assert result["current_tier"] == 2


def test_tier_caps_at_max(conn):
    ensure_rival_progress(conn, "player1")
    # Advance through all tiers
    for _ in range(MAX_RIVAL_TIER * WINS_TO_ADVANCE * 2):
        record_rival_attempt(conn, "player1", won=True)
    progress = get_rival_progress(conn, "player1")
    assert progress["current_tier"] <= MAX_RIVAL_TIER


def test_get_rival_tier_default(conn):
    assert get_rival_tier(conn, "new_player") == 1


def test_get_rival_tier_after_advance(conn):
    ensure_rival_progress(conn, "player1")
    for _ in range(WINS_TO_ADVANCE):
        record_rival_attempt(conn, "player1", won=True)
    assert get_rival_tier(conn, "player1") == 2


def test_uses_write_lock():
    assert isinstance(_write_lock, type(threading.Lock()))


def test_constants():
    assert WINS_TO_ADVANCE == 2
    assert MAX_RIVAL_TIER == 5
