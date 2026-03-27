"""Tests for graduation detection and API endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.db import create_api_key, create_player, init_db
from server.rival_db import (
    WINS_TO_ADVANCE,
    ensure_rival_progress,
    get_rival_progress,
    init_rival_table,
    is_graduated,
    record_graduation,
    record_rival_attempt,
)


@pytest.fixture
def conn():
    db = init_db(":memory:")
    return db


@pytest.fixture(autouse=True)
def setup_app_db():
    old_db = getattr(app.state, "db", None)
    app.state.db = init_db(":memory:")
    yield
    app.state.db = old_db


client = TestClient(app)


# ── Cycle 1: is_graduated logic ──────────────────────────────────────


class TestIsGraduated:
    def test_not_graduated_new_player(self, conn):
        assert is_graduated(conn, "new_player") is False

    def test_not_graduated_tier_4(self, conn):
        ensure_rival_progress(conn, "p1")
        # Advance to tier 4 (clear tiers 1-3 = 3 * WINS_TO_ADVANCE wins)
        for _ in range(WINS_TO_ADVANCE * 3):
            record_rival_attempt(conn, "p1", won=True)
        progress = get_rival_progress(conn, "p1")
        assert progress["current_tier"] == 4
        assert is_graduated(conn, "p1") is False

    def test_graduated_after_tier_5_cleared(self, conn):
        ensure_rival_progress(conn, "p1")
        # Advance through all 5 tiers
        for _ in range(WINS_TO_ADVANCE * 5):
            record_rival_attempt(conn, "p1", won=True)
        assert is_graduated(conn, "p1") is True

    def test_graduation_sets_timestamp(self, conn):
        ensure_rival_progress(conn, "p1")
        for _ in range(WINS_TO_ADVANCE * 5):
            record_rival_attempt(conn, "p1", won=True)
        progress = get_rival_progress(conn, "p1")
        assert progress["graduated_at"] is not None

    def test_record_graduation_explicit(self, conn):
        ensure_rival_progress(conn, "p1")
        record_graduation(conn, "p1")
        assert is_graduated(conn, "p1") is True


# ── Cycle 2: idempotent migration ────────────────────────────────────


class TestMigration:
    def test_graduated_at_column_migration_idempotent(self, conn):
        # init_rival_table called twice should not error
        init_rival_table(conn)
        init_rival_table(conn)


# ── Cycle 3: API endpoint ────────────────────────────────────────────


class TestGraduationAPI:
    def test_graduated_endpoint_returns_200(self):
        create_player(app.state.db, "p1", "Test")
        key = create_api_key(app.state.db, "p1")
        resp = client.get("/api/rival/graduated", headers={"X-API-Key": key})
        assert resp.status_code == 200

    def test_graduated_false_for_new_player(self):
        create_player(app.state.db, "p1", "Test")
        key = create_api_key(app.state.db, "p1")
        resp = client.get("/api/rival/graduated", headers={"X-API-Key": key})
        data = resp.json()
        assert data["graduated"] is False
        assert data["graduated_at"] is None

    def test_graduated_true_after_clearing(self):
        create_player(app.state.db, "p1", "Test")
        key = create_api_key(app.state.db, "p1")
        ensure_rival_progress(app.state.db, "p1")
        for _ in range(WINS_TO_ADVANCE * 5):
            record_rival_attempt(app.state.db, "p1", won=True)
        resp = client.get("/api/rival/graduated", headers={"X-API-Key": key})
        data = resp.json()
        assert data["graduated"] is True
        assert data["graduated_at"] is not None

    def test_tiers_beaten_count(self):
        create_player(app.state.db, "p1", "Test")
        key = create_api_key(app.state.db, "p1")
        ensure_rival_progress(app.state.db, "p1")
        for _ in range(WINS_TO_ADVANCE * 5):
            record_rival_attempt(app.state.db, "p1", won=True)
        resp = client.get("/api/rival/graduated", headers={"X-API-Key": key})
        assert resp.json()["tiers_beaten"] == 5

    def test_graduated_requires_auth(self):
        resp = client.get("/api/rival/graduated")
        assert resp.status_code == 401
