"""Tests for engine.profile_db — SQLite player profile persistence."""

import sqlite3

import pytest

from engine.profile_db import (
    get_or_create_profile,
    get_profile,
    init_profile_db,
    list_profiles,
    get_leaderboard,
    update_profile,
)


@pytest.fixture
def conn():
    """In-memory profile DB connection, closed after test."""
    c = init_profile_db(":memory:")
    yield c
    c.close()


# ---------------------------------------------------------------------------
# Cycle 1: init_profile_db
# ---------------------------------------------------------------------------


def test_init_profile_db_returns_connection():
    """init_profile_db returns an open sqlite3 Connection."""
    from engine.profile_db import init_profile_db

    conn = init_profile_db(":memory:")
    assert isinstance(conn, sqlite3.Connection)
    conn.close()


def test_init_profile_db_creates_profiles_table():
    """The profiles table exists after init."""
    from engine.profile_db import init_profile_db

    conn = init_profile_db(":memory:")
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='profiles'"
    )
    assert cur.fetchone() is not None
    conn.close()


def test_init_profile_db_idempotent():
    """Calling init_profile_db twice on the same DB does not raise."""
    from engine.profile_db import init_profile_db

    conn = init_profile_db(":memory:")
    # Insert a row, then re-init on the same connection's DB
    conn.execute(
        "INSERT INTO profiles (name, total_xp, level, matches, wins, kills, created_at, updated_at) "
        "VALUES ('alice', 0, 1, 0, 0, 0, '2026-01-01', '2026-01-01')"
    )
    conn.commit()
    # Re-init should not drop the table
    conn2 = init_profile_db(":memory:")
    # Original conn still has its data
    row = conn.execute("SELECT * FROM profiles WHERE name='alice'").fetchone()
    assert row is not None
    conn.close()
    conn2.close()


def test_init_profile_db_row_factory():
    """Connection uses sqlite3.Row row factory for dict-like access."""
    from engine.profile_db import init_profile_db

    conn = init_profile_db(":memory:")
    assert conn.row_factory is sqlite3.Row
    conn.close()


# ---------------------------------------------------------------------------
# Cycle 2: get_or_create_profile / get_profile
# ---------------------------------------------------------------------------


def test_get_or_create_profile_creates_new(conn):
    """First call creates a profile with default values."""
    profile = get_or_create_profile(conn, "alice")
    assert profile["name"] == "alice"
    assert profile["total_xp"] == 0
    assert profile["level"] == 1
    assert profile["matches"] == 0
    assert profile["wins"] == 0
    assert profile["kills"] == 0


def test_get_or_create_profile_returns_existing(conn):
    """Second call returns the same profile, not a new one."""
    p1 = get_or_create_profile(conn, "alice")
    p2 = get_or_create_profile(conn, "alice")
    assert p1["created_at"] == p2["created_at"]


def test_get_profile_returns_none_for_missing(conn):
    """get_profile returns None when name does not exist."""
    assert get_profile(conn, "nobody") is None


def test_get_profile_returns_existing(conn):
    """get_profile returns an existing profile."""
    get_or_create_profile(conn, "bob")
    profile = get_profile(conn, "bob")
    assert profile is not None
    assert profile["name"] == "bob"


# ---------------------------------------------------------------------------
# Cycle 3: update_profile
# ---------------------------------------------------------------------------


def test_update_profile_accumulates_xp(conn):
    """XP earned is added to total_xp."""
    update_profile(conn, "alice", xp_earned=100, kills=0, won=False)
    update_profile(conn, "alice", xp_earned=50, kills=0, won=False)
    p = get_profile(conn, "alice")
    assert p["total_xp"] == 150


def test_update_profile_increments_matches(conn):
    """Each update_profile call increments matches by 1."""
    update_profile(conn, "alice", xp_earned=0, kills=0, won=False)
    update_profile(conn, "alice", xp_earned=0, kills=0, won=True)
    p = get_profile(conn, "alice")
    assert p["matches"] == 2


def test_update_profile_increments_wins(conn):
    """Wins only increment when won=True."""
    update_profile(conn, "alice", xp_earned=0, kills=0, won=False)
    update_profile(conn, "alice", xp_earned=0, kills=0, won=True)
    update_profile(conn, "alice", xp_earned=0, kills=0, won=True)
    p = get_profile(conn, "alice")
    assert p["wins"] == 2


def test_update_profile_accumulates_kills(conn):
    """Kills accumulate across updates."""
    update_profile(conn, "alice", xp_earned=0, kills=3, won=False)
    update_profile(conn, "alice", xp_earned=0, kills=2, won=False)
    p = get_profile(conn, "alice")
    assert p["kills"] == 5


def test_update_profile_upserts_new_player(conn):
    """update_profile creates the profile if it doesn't exist yet."""
    p = update_profile(conn, "newbie", xp_earned=50, kills=1, won=True)
    assert p["name"] == "newbie"
    assert p["total_xp"] == 50
    assert p["matches"] == 1
    assert p["wins"] == 1
    assert p["kills"] == 1


def test_update_profile_returns_updated_dict(conn):
    """update_profile returns the updated profile as a dict."""
    result = update_profile(conn, "alice", xp_earned=200, kills=5, won=True)
    assert isinstance(result, dict)
    assert result["total_xp"] == 200
    assert result["kills"] == 5


# ---------------------------------------------------------------------------
# Cycle 4: list_profiles / get_leaderboard
# ---------------------------------------------------------------------------


def test_list_profiles_empty(conn):
    """list_profiles returns empty list when no profiles exist."""
    assert list_profiles(conn) == []


def test_list_profiles_ordered_by_level(conn):
    """Profiles are ordered by level descending by default."""
    # Give different XP to get potentially different levels
    update_profile(conn, "low", xp_earned=10, kills=0, won=False)
    update_profile(conn, "high", xp_earned=9999, kills=0, won=False)
    profiles = list_profiles(conn)
    assert len(profiles) == 2
    # Higher XP/level should come first
    assert profiles[0]["name"] == "high"


def test_list_profiles_respects_limit(conn):
    """list_profiles respects the limit parameter."""
    for i in range(5):
        update_profile(conn, f"bot_{i}", xp_earned=i * 10, kills=0, won=False)
    profiles = list_profiles(conn, limit=3)
    assert len(profiles) == 3


def test_get_leaderboard_empty(conn):
    """get_leaderboard returns empty list when no profiles exist."""
    assert get_leaderboard(conn) == []


def test_get_leaderboard_ordered_by_level_then_xp(conn):
    """Leaderboard sorts by level DESC, then total_xp DESC."""
    update_profile(conn, "a", xp_earned=100, kills=0, won=False)
    update_profile(conn, "b", xp_earned=200, kills=0, won=False)
    update_profile(conn, "c", xp_earned=50, kills=0, won=False)
    lb = get_leaderboard(conn)
    assert lb[0]["name"] == "b"
    assert lb[-1]["name"] == "c"


def test_get_leaderboard_respects_limit(conn):
    """get_leaderboard respects the limit parameter."""
    for i in range(15):
        update_profile(conn, f"bot_{i}", xp_earned=i * 10, kills=0, won=False)
    lb = get_leaderboard(conn, limit=5)
    assert len(lb) == 5


# ---------------------------------------------------------------------------
# Cycle 5: Level recalculation
# ---------------------------------------------------------------------------


def test_update_profile_recalculates_level(conn):
    """Level is recalculated from total XP on every update."""
    # 100 XP should be level 2 per the level table
    p = update_profile(conn, "alice", xp_earned=100, kills=0, won=False)
    assert p["level"] >= 2

    # 1000 XP should be a higher level
    p = update_profile(conn, "alice", xp_earned=900, kills=0, won=False)
    assert p["total_xp"] == 1000
    assert p["level"] > 2


def test_level_starts_at_one_for_zero_xp(conn):
    """A new profile with 0 XP is level 1."""
    p = get_or_create_profile(conn, "newbie")
    assert p["level"] == 1
