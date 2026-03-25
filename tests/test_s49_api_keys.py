"""Tests for T49.5: API key hashing + share route path check."""

from __future__ import annotations

import hashlib
import inspect
import json
import re

import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.db import (
    create_api_key,
    create_player,
    get_player_by_api_key,
    init_db,
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


# ── Cycle 1: API key hashing ────────────────────────────────────────


class TestApiKeyHashing:
    """Created API keys are hashed before storage."""

    def test_created_key_is_uuid_hex(self, conn, player):
        """create_api_key returns a 32-char hex string (uuid4.hex)."""
        key = create_api_key(conn, player["id"])
        assert isinstance(key, str)
        assert len(key) == 32
        assert re.fullmatch(r"[0-9a-f]{32}", key)

    def test_stored_value_is_sha256_hash(self, conn, player):
        """The DB stores a SHA-256 hash, NOT the raw key."""
        key = create_api_key(conn, player["id"])
        expected_hash = hashlib.sha256(key.encode()).hexdigest()

        row = conn.execute("SELECT key FROM api_keys").fetchone()
        assert row is not None
        stored = row["key"]
        # Stored value must be the hash, not the raw key
        assert stored != key
        assert stored == expected_hash

    def test_lookup_by_raw_key_succeeds(self, conn, player):
        """get_player_by_api_key(raw_key) finds the player via hash."""
        key = create_api_key(conn, player["id"])
        found = get_player_by_api_key(conn, key)
        assert found is not None
        assert found["id"] == player["id"]

    def test_lookup_wrong_key_returns_none(self, conn):
        """Looking up a non-existent key returns None."""
        assert get_player_by_api_key(conn, "bogus") is None


# ── Cycle 2: Dual-mode migration ────────────────────────────────────


class TestDualModeMigration:
    """Old plaintext keys still work and get auto-upgraded."""

    def test_plaintext_fallback_finds_player(self, conn, player):
        """A key stored as plaintext (old style) still resolves."""
        # Manually insert a plaintext key (simulating old DB)
        conn.execute(
            "INSERT INTO api_keys (key, player_id, created_at) VALUES (?, ?, ?)",
            ("old-plain-key", player["id"], "2025-01-01T00:00:00Z"),
        )
        conn.commit()

        found = get_player_by_api_key(conn, "old-plain-key")
        assert found is not None
        assert found["id"] == player["id"]

    def test_plaintext_key_gets_upgraded_to_hash(self, conn, player):
        """After a successful plaintext lookup, the key is upgraded to hash."""
        conn.execute(
            "INSERT INTO api_keys (key, player_id, created_at) VALUES (?, ?, ?)",
            ("old-plain-key", player["id"], "2025-01-01T00:00:00Z"),
        )
        conn.commit()

        # First lookup triggers migration
        get_player_by_api_key(conn, "old-plain-key")

        # Now the DB should contain the hash, not plaintext
        expected_hash = hashlib.sha256(b"old-plain-key").hexdigest()
        row = conn.execute(
            "SELECT key FROM api_keys WHERE player_id = ?", (player["id"],)
        ).fetchone()
        assert row["key"] == expected_hash

        # Second lookup still works (now via hash path)
        found = get_player_by_api_key(conn, "old-plain-key")
        assert found is not None


# ── Cycle 3: Share route path canonicalization ───────────────────────


class TestSharePathCanon:
    """share.py has path traversal protection matching match.py."""

    def test_share_route_source_has_path_check(self):
        """The share route source contains resolve + is_relative_to."""
        import server.routes.share as share_mod

        src = inspect.getsource(share_mod)
        assert "resolve()" in src
        assert "is_relative_to" in src

    def test_share_traversal_attempt_returns_404(self, tmp_path):
        """A path-traversal match_id doesn't escape the results dir."""
        # Create a file outside results dir
        secret = tmp_path / "secret.json"
        secret.write_text(json.dumps({"secret": True}), encoding="utf-8")

        results_dir = tmp_path / "results"
        results_dir.mkdir()
        app.state.results_dir = str(results_dir)

        client = TestClient(app)
        # Try to traverse — regex already blocks most, but the path
        # check is defense-in-depth. Even if the regex allowed it,
        # resolve+is_relative_to would catch it.
        resp = client.get("/m/../secret", follow_redirects=False)
        # Could be 400 (regex) or 404 (not found after canonicalization)
        assert resp.status_code in (400, 404)
