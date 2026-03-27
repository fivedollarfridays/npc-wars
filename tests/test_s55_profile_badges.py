"""Tests for profile page badge display (T55.5)."""

from pathlib import Path

from fastapi.testclient import TestClient

from server.app import app
from server.db import init_db


class TestProfileBadgeHTML:
    """Profile page HTML contains badge elements."""

    def test_profile_has_badges_section(self) -> None:
        html = Path("server/static/profile.html").read_text()
        assert "badge" in html.lower()

    def test_profile_fetches_badge_api(self) -> None:
        html = Path("server/static/profile.html").read_text()
        assert "/api/badges/" in html

    def test_profile_has_badge_container(self) -> None:
        html = Path("server/static/profile.html").read_text()
        assert "badge-grid" in html

    def test_profile_shows_earned_styling(self) -> None:
        html = Path("server/static/profile.html").read_text()
        assert "earned" in html.lower()


class TestProfilePageLoads:
    """Profile page serves successfully."""

    def test_profile_page_loads(self) -> None:
        old_db = getattr(app.state, "db", None)
        app.state.db = init_db(":memory:")
        client = TestClient(app)
        resp = client.get("/profile/test_player")
        assert resp.status_code == 200
        app.state.db = old_db
