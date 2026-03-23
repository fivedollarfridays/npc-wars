"""Tests for player auth + bot persistence (T42.1)."""

from __future__ import annotations

import pytest

from server.db import (
    create_api_key,
    create_player,
    get_bot,
    get_player_bots,
    get_player_by_api_key,
    init_db,
    store_bot,
)


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture()
def conn(tmp_path):
    """Fresh DB connection with all tables."""
    c = init_db(str(tmp_path / "test.db"))
    yield c
    c.close()


@pytest.fixture()
def player(conn):
    """A player in the DB."""
    return create_player(conn, "p1", "Alice")


# ── 1. Schema ────────────────────────────────────────────────────────


class TestSchema:
    """init_db creates api_keys and bots tables."""

    def test_api_keys_table_exists(self, conn):
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        names = {r["name"] for r in tables}
        assert "api_keys" in names

    def test_bots_table_exists(self, conn):
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        names = {r["name"] for r in tables}
        assert "bots" in names


# ── 2. API Key CRUD ──────────────────────────────────────────────────


class TestApiKeys:
    """create_api_key / get_player_by_api_key."""

    def test_create_returns_string(self, conn, player):
        key = create_api_key(conn, player["id"])
        assert isinstance(key, str)
        assert len(key) >= 16

    def test_lookup_valid_key(self, conn, player):
        key = create_api_key(conn, player["id"])
        found = get_player_by_api_key(conn, key)
        assert found is not None
        assert found["id"] == player["id"]
        assert found["name"] == "Alice"

    def test_lookup_invalid_key(self, conn):
        assert get_player_by_api_key(conn, "bogus-key") is None

    def test_multiple_keys_same_player(self, conn, player):
        k1 = create_api_key(conn, player["id"])
        k2 = create_api_key(conn, player["id"])
        assert k1 != k2
        assert get_player_by_api_key(conn, k1) is not None
        assert get_player_by_api_key(conn, k2) is not None


# ── 3. Bot CRUD ──────────────────────────────────────────────────────


class TestBotCrud:
    """store_bot / get_bot / get_player_bots."""

    BOT_SOURCE = 'BOT_NAME = "Foo"\ndef decide(state): return "north"\n'

    def test_store_returns_id(self, conn, player):
        bot_id = store_bot(conn, player["id"], "Foo", "F", self.BOT_SOURCE)
        assert isinstance(bot_id, int)
        assert bot_id > 0

    def test_get_bot(self, conn, player):
        bot_id = store_bot(conn, player["id"], "Foo", "F", self.BOT_SOURCE)
        bot = get_bot(conn, bot_id)
        assert bot is not None
        assert bot["name"] == "Foo"
        assert bot["emoji"] == "F"
        assert bot["source"] == self.BOT_SOURCE
        assert bot["player_id"] == player["id"]

    def test_get_nonexistent_bot(self, conn):
        assert get_bot(conn, 9999) is None

    def test_get_player_bots(self, conn, player):
        store_bot(conn, player["id"], "A", "a", "src_a")
        store_bot(conn, player["id"], "B", "b", "src_b")
        bots = get_player_bots(conn, player["id"])
        assert len(bots) == 2
        names = {b["name"] for b in bots}
        assert names == {"A", "B"}

    def test_player_bots_empty(self, conn, player):
        bots = get_player_bots(conn, player["id"])
        assert bots == []

    def test_bots_isolated_by_player(self, conn, player):
        p2 = create_player(conn, "p2", "Bob")
        store_bot(conn, player["id"], "A", "a", "src_a")
        store_bot(conn, p2["id"], "B", "b", "src_b")
        assert len(get_player_bots(conn, player["id"])) == 1
        assert len(get_player_bots(conn, p2["id"])) == 1
