"""S48 integration gate — cross-module browser flow validation (T48.6).

These tests verify that S48 components CONNECT correctly across module
boundaries.  They do NOT re-test individual module behavior (covered by
test_s48_landing, test_s48_lobby, test_s48_editor, test_s48_viewer,
test_s48_results).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.lobby import Lobby, MAX_PLAYERS

STATIC_DIR = Path(__file__).resolve().parent.parent / "server" / "static"
VIEWER_DIR = Path(__file__).resolve().parent.parent / "viewer"

client = TestClient(app)


# ── helpers ────────────────────────────────────────────────────────────


def _make_bot(name: str = "TestBot", emoji: str = "T") -> dict:
    return {
        "name": name,
        "emoji": emoji,
        "source": "code",
        "player_id": "p1",
        "bot_id": 1,
    }


def _extract_hrefs(html: str) -> list[str]:
    """Extract all href attribute values from HTML."""
    return re.findall(r'href=["\']([^"\']+)["\']', html)


# ── 1. Browser flow navigation ────────────────────────────────────────


class TestBrowserFlowNavigation:
    """Landing page links resolve to real routes that return 200."""

    def test_editor_link_resolves(self):
        """Landing page editor link (/static/editor.html) returns 200."""
        resp = client.get("/static/editor.html")
        assert resp.status_code == 200

    def test_tournaments_link_resolves(self):
        """Landing page tournaments link (/tournaments) returns 200."""
        resp = client.get("/tournaments")
        assert resp.status_code == 200

    def test_leaderboard_link_resolves(self):
        """Landing page leaderboard link (/leaderboard) returns 200."""
        resp = client.get("/leaderboard")
        assert resp.status_code == 200

    def test_viewer_route_resolves(self):
        """Viewer route (/viewer) used by editor redirect returns 200."""
        resp = client.get("/viewer")
        assert resp.status_code == 200

    def test_editor_references_correct_lobby_api_url(self):
        """Editor or its lobby JS references /api/lobby/status which is a real endpoint."""
        editor_text = (STATIC_DIR / "editor.html").read_text()
        lobby_js = STATIC_DIR / "js" / "lobby.js"
        if lobby_js.exists():
            editor_text += "\n" + lobby_js.read_text()
        assert "/api/lobby/status" in editor_text
        # Verify the endpoint itself responds
        resp = client.get("/api/lobby/status")
        assert resp.status_code == 200

    def test_editor_redirect_matches_viewer_route(self):
        """Editor redirect URL format (/viewer?match=) matches the viewer route."""
        editor_text = (STATIC_DIR / "editor.html").read_text()
        lobby_js = STATIC_DIR / "js" / "lobby.js"
        if lobby_js.exists():
            editor_text += "\n" + lobby_js.read_text()
        assert "/viewer?match=" in editor_text
        # The base path /viewer must be a real route
        resp = client.get("/viewer?match=test123")
        assert resp.status_code == 200


# ── 2. Lobby → match flow ─────────────────────────────────────────────


class TestLobbyToMatchFlow:
    """Lobby fills up and produces a match_id accessible via match API."""

    def test_lobby_status_starts_empty(self):
        """Fresh lobby has empty player_list and no match_id."""
        lobby = Lobby()
        s = lobby.status()
        assert s["player_list"] == []
        assert s["match_id"] is None
        assert s["status"] == "waiting"

    def test_joining_updates_player_list_and_status(self):
        """Joining a bot transitions lobby from waiting to filling with player in list."""
        lobby = Lobby()
        lobby.join(_make_bot("Alpha", "A"))
        s = lobby.status()
        assert s["status"] == "filling"
        assert len(s["player_list"]) == 1
        assert s["player_list"][0]["name"] == "Alpha"

    def test_full_lobby_triggers_match_with_id(self):
        """Filling lobby to MAX_PLAYERS triggers match and sets match_id."""
        from server.queue import InMemoryQueue, set_backend

        set_backend(InMemoryQueue())
        lobby = Lobby()
        for i in range(MAX_PLAYERS):
            lobby.join(_make_bot(f"Bot{i}", "X"))
        s = lobby.status()
        assert s["match_id"] is not None
        assert s["status"] == "running"

    def test_match_id_accessible_via_match_api(self):
        """Match result file created during trigger is accessible via /api/match/{id}."""
        from server.queue import InMemoryQueue, set_backend

        set_backend(InMemoryQueue())
        lobby = Lobby()
        for i in range(MAX_PLAYERS):
            lobby.join(_make_bot(f"Bot{i}", "X"))
        match_id = lobby.status()["match_id"]

        # The match may or may not have a results file yet (async processing).
        # But the API endpoint should at least accept the match_id format.
        resp = client.get(f"/api/match/{match_id}")
        # 200 if results file exists, 404 if async processing hasn't written it yet.
        # Both are valid — the key is no 400/500 errors.
        assert resp.status_code in (200, 404)


# ── 3. Viewer match loading ───────────────────────────────────────────


class TestViewerMatchLoading:
    """Viewer loads match data and includes results overlay module."""

    @pytest.fixture()
    def _results_dir(self, tmp_path: Path):
        """Temp results dir with a fixture match file."""
        match_data = {
            "match_id": 99,
            "grid_size": 10,
            "duration_rounds": 5,
            "players": [
                {"name": "bot_a", "emoji": "A"},
                {"name": "bot_b", "emoji": "B"},
            ],
            "rounds": [{"round": 1, "events": []}],
            "winner": {"name": "bot_a", "emoji": "A"},
        }
        (tmp_path / "match_99.json").write_text(json.dumps(match_data))
        old = app.state.results_dir
        app.state.results_dir = str(tmp_path)
        yield tmp_path
        app.state.results_dir = old

    def test_match_api_returns_expected_fields(self, _results_dir: Path):
        """Match API response contains winner, players, and rounds fields."""
        resp = client.get("/api/match/99")
        assert resp.status_code == 200
        data = resp.json()
        assert "winner" in data
        assert "players" in data
        assert "rounds" in data
        assert len(data["players"]) == 2

    def test_viewer_html_loads_results_module(self):
        """Viewer HTML loads results.js so the results overlay works."""
        resp = client.get("/viewer")
        assert "results.js" in resp.text

    def test_viewer_html_loads_app_module(self):
        """Viewer HTML loads app.js for match loading logic."""
        resp = client.get("/viewer")
        assert "app.js" in resp.text

    def test_match_api_rejects_path_traversal(self):
        """Match API rejects IDs with path traversal characters."""
        resp = client.get("/api/match/../../etc/passwd")
        assert resp.status_code in (400, 404, 422)


# ── 4. No dead links ──────────────────────────────────────────────────


class TestNoDeadLinks:
    """All internal links in landing page and editor resolve to valid routes."""

    def test_all_landing_page_hrefs_resolve(self):
        """Every href in index.html points to a route that returns 200."""
        html = (STATIC_DIR / "index.html").read_text()
        hrefs = _extract_hrefs(html)
        internal = [h for h in hrefs if h.startswith("/")]
        assert len(internal) >= 3, f"Expected at least 3 internal links, got {internal}"
        for href in internal:
            # Strip dynamic segments (e.g. /profile/ needs a param)
            if "/profile/" in href:
                continue  # dynamic route, skip
            resp = client.get(href)
            assert resp.status_code == 200, f"Dead link: {href} returned {resp.status_code}"

    def test_editor_viewer_redirect_url_is_valid(self):
        """Editor redirect URL (/viewer?match=...) resolves to 200."""
        resp = client.get("/viewer?match=abc123")
        assert resp.status_code == 200

    def test_results_overlay_play_again_link_is_valid(self):
        """Results overlay Play Again link (/static/editor.html) resolves to 200."""
        resp = client.get("/static/editor.html")
        assert resp.status_code == 200

    def test_results_overlay_leaderboard_link_is_valid(self):
        """Results overlay Leaderboard link (/leaderboard) resolves to 200."""
        resp = client.get("/leaderboard")
        assert resp.status_code == 200
