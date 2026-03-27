"""Badge system tests — definitions, query function, API endpoint."""

import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.db import init_db, create_player
from server.rival_db import ensure_rival_progress, record_rival_attempt, WINS_TO_ADVANCE
from server.badges import get_player_badges, TIER_BADGES, GRADUATION_BADGE


@pytest.fixture(autouse=True)
def setup_db():
    old_db = getattr(app.state, "db", None)
    app.state.db = init_db(":memory:")
    yield
    app.state.db = old_db


client = TestClient(app)


class TestBadgeDefinitions:
    def test_tier_badges_has_5_entries(self):
        assert len(TIER_BADGES) == 5

    def test_each_tier_badge_has_required_fields(self):
        for tier, badge in TIER_BADGES.items():
            assert "name" in badge
            assert "emoji" in badge
            assert "description" in badge

    def test_graduation_badge_exists(self):
        assert "name" in GRADUATION_BADGE
        assert "emoji" in GRADUATION_BADGE


class TestGetPlayerBadges:
    def test_new_player_no_earned_badges(self):
        conn = app.state.db
        create_player(conn, "p1", "Test")
        badges = get_player_badges(conn, "p1")
        earned = [b for b in badges if b["earned"]]
        assert len(earned) == 0

    def test_tier_2_player_has_tier_1_badge(self):
        conn = app.state.db
        create_player(conn, "p1", "Test")
        ensure_rival_progress(conn, "p1")
        for _ in range(WINS_TO_ADVANCE):
            record_rival_attempt(conn, "p1", won=True)
        badges = get_player_badges(conn, "p1")
        earned = [b for b in badges if b["earned"]]
        assert len(earned) == 1
        assert earned[0]["tier"] == 1

    def test_graduated_player_has_all_badges(self):
        conn = app.state.db
        create_player(conn, "p1", "Test")
        ensure_rival_progress(conn, "p1")
        for _ in range(WINS_TO_ADVANCE * 5):
            record_rival_attempt(conn, "p1", won=True)
        badges = get_player_badges(conn, "p1")
        earned = [b for b in badges if b["earned"]]
        # 5 tier badges + 1 graduation = 6
        assert len(earned) == 6

    def test_badges_include_unearned(self):
        conn = app.state.db
        create_player(conn, "p1", "Test")
        badges = get_player_badges(conn, "p1")
        assert len(badges) == 6  # 5 tiers + graduation, all unearned


class TestBadgeAPI:
    def test_endpoint_returns_200(self):
        create_player(app.state.db, "p1", "Test")
        resp = client.get("/api/badges/p1")
        assert resp.status_code == 200

    def test_endpoint_returns_badge_list(self):
        create_player(app.state.db, "p1", "Test")
        resp = client.get("/api/badges/p1")
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 6

    def test_endpoint_unknown_player(self):
        resp = client.get("/api/badges/nonexistent")
        assert resp.status_code == 200  # Returns all unearned

    def test_no_auth_required(self):
        create_player(app.state.db, "p1", "Test")
        resp = client.get("/api/badges/p1")  # No X-API-Key header
        assert resp.status_code == 200
