"""Server integration test suite — exercises all S17 endpoints and flows (T17.10)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.routes.submit import clear_rate_limits


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clear_rate_limits():
    """Reset rate limit state before each test to avoid interference."""
    clear_rate_limits()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


MATCH_FIXTURE: dict = {
    "match_id": 1,
    "winner": "\U0001f916",
    "duration_rounds": 10,
    "grid_size": 10,
    "players": [
        {"emoji": "\U0001f916", "name": "Bot1"},
        {"emoji": "\U0001f3af", "name": "Bot2"},
    ],
    "stats": {
        "\U0001f916": {"kills": 3, "damage_dealt": 100, "damage_taken": 50},
        "\U0001f3af": {"kills": 1, "damage_dealt": 60, "damage_taken": 80},
    },
    "eliminations": [
        {"round": 8, "emoji": "\U0001f3af", "cause": "kill", "killed_by": "\U0001f916"}
    ],
    "diff": {},
}


@pytest.fixture()
def results_dir(tmp_path):
    """Create a tmp results dir with fixture match data and wire into app."""
    rdir = tmp_path / "results"
    rdir.mkdir()
    (rdir / "match_001.json").write_text(json.dumps(MATCH_FIXTURE))

    # Second match for stats/leaderboard aggregation
    match2 = {
        **MATCH_FIXTURE,
        "match_id": 2,
        "winner": "\U0001f3af",
        "stats": {
            "\U0001f916": {"kills": 1, "damage_dealt": 80, "damage_taken": 60},
            "\U0001f3af": {"kills": 2, "damage_dealt": 90, "damage_taken": 40},
        },
        "eliminations": [
            {"round": 7, "emoji": "\U0001f916", "cause": "kill", "killed_by": "\U0001f3af"}
        ],
    }
    (rdir / "match_002.json").write_text(json.dumps(match2))

    old_dir = getattr(app.state, "results_dir", "results")
    app.state.results_dir = str(rdir)
    yield rdir
    app.state.results_dir = old_dir


# ── 1. TestHealth ────────────────────────────────────────────────────


class TestHealth:
    """GET /health returns 200 {"status": "ok"}."""

    def test_health_status_ok(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "components" in data

    def test_health_cors_present(self, client: TestClient):
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:8000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:8000"


# ── 2. TestBotSubmission ─────────────────────────────────────────────


class TestBotSubmission:
    """POST /api/submit-bot validates source and returns 202 or 400."""

    VALID_SOURCE = (
        'BOT_NAME = "TestBot"\n'
        'BOT_EMOJI = "T"\n'
        "def decide(state):\n"
        '    return "north"\n'
    )

    def test_valid_source_returns_202(self, client: TestClient):
        resp = client.post("/api/submit-bot", json={"source": self.VALID_SOURCE})
        assert resp.status_code == 202
        assert "job_id" in resp.json()

    def test_import_os_returns_400(self, client: TestClient):
        bad_source = "import os\ndef decide(state): return 'north'\n"
        resp = client.post("/api/submit-bot", json={"source": bad_source})
        assert resp.status_code == 400
        body = resp.json()
        assert "detail" in body
        assert len(body["detail"]) > 0

    def test_empty_source_returns_400(self, client: TestClient):
        resp = client.post("/api/submit-bot", json={"source": "  "})
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_rate_limit_returns_429(self, client: TestClient):
        # First submission succeeds
        resp1 = client.post("/api/submit-bot", json={"source": self.VALID_SOURCE})
        assert resp1.status_code == 202
        # Second immediate submission is rate-limited
        resp2 = client.post("/api/submit-bot", json={"source": self.VALID_SOURCE})
        assert resp2.status_code == 429


# ── 3. TestMatchRetrieval ────────────────────────────────────────────


class TestMatchRetrieval:
    """GET /api/match/{match_id} returns match JSON or 404."""

    def test_existing_match_returns_200(self, client: TestClient, results_dir):
        resp = client.get("/api/match/001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["match_id"] == 1
        assert data["winner"] == "\U0001f916"
        assert "players" in data
        assert "stats" in data

    def test_missing_match_returns_404(self, client: TestClient, results_dir):
        resp = client.get("/api/match/999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Match not found"

    def test_match_includes_diff(self, client: TestClient, results_dir):
        resp = client.get("/api/match/001")
        assert "diff" in resp.json()


# ── 4. TestStats ─────────────────────────────────────────────────────


class TestStats:
    """GET /api/stats/{player_id} returns averages or 404."""

    def test_known_player_returns_stats(self, client: TestClient, results_dir):
        resp = client.get("/api/stats/%F0%9F%A4%96")  # URL-encoded robot emoji
        assert resp.status_code == 200
        data = resp.json()
        # Robot across 2 matches: kills avg (3+1)/2=2.0
        assert data["kills"] == pytest.approx(2.0)
        assert data["damage_dealt"] == pytest.approx(90.0)

    def test_unknown_player_returns_404(self, client: TestClient, results_dir):
        resp = client.get("/api/stats/%F0%9F%91%BB")  # ghost emoji
        assert resp.status_code == 404
        assert "detail" in resp.json()


# ── 5. TestLeaderboard ───────────────────────────────────────────────


class TestLeaderboard:
    """GET /api/leaderboard returns ranked list."""

    def test_leaderboard_returns_ranked_list(self, client: TestClient, results_dir):
        resp = client.get("/api/leaderboard")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        emojis = {e["emoji"] for e in data}
        assert "\U0001f916" in emojis
        assert "\U0001f3af" in emojis

    def test_leaderboard_sort_by_kills(self, client: TestClient, results_dir):
        resp = client.get("/api/leaderboard?sort_by=kills")
        assert resp.status_code == 200
        data = resp.json()
        # Robot: 3+1=4 kills, Target: 1+2=3 kills
        assert data[0]["emoji"] == "\U0001f916"


# ── 6. TestEditorPage ────────────────────────────────────────────────


class TestEditorPage:
    """GET /static/editor.html returns HTML."""

    def test_editor_returns_200_html(self, client: TestClient):
        resp = client.get("/static/editor.html")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        assert "<html" in resp.text.lower() or "<!doctype" in resp.text.lower()


# ── 7. TestLobbyFlow ─────────────────────────────────────────────────


class TestLobbyFlow:
    """Lobby collects players, fills AI, and triggers match."""

    def test_join_and_status(self):
        from server.lobby import Lobby

        lobby = Lobby()
        assert lobby.status()["players"] == 0

        lobby.join({"name": "P1", "emoji": "A"})
        st = lobby.status()
        assert st["players"] == 1
        assert st["triggered"] is False

    def test_capacity_trigger(self):
        from server.lobby import Lobby, MAX_PLAYERS
        from server.queue import InMemoryQueue, set_backend

        q = InMemoryQueue()
        set_backend(q)
        lobby = Lobby()
        for i in range(MAX_PLAYERS):
            lobby.join({"name": f"P{i}", "emoji": str(i)})
        assert lobby.status()["triggered"] is True

    def test_timer_trigger(self):
        import time
        from unittest.mock import patch

        from server.lobby import LOBBY_TIMEOUT, Lobby

        lobby = Lobby()
        lobby.join({"name": "P1", "emoji": "A"})

        # Fast-forward time past the timeout; mock enqueue to avoid JSON
        # serialization of fill bot decide_func callables
        with (
            patch.object(time, "monotonic", side_effect=[
                lobby._start_time + LOBBY_TIMEOUT + 1,
            ]),
            patch("server.lobby.enqueue_match") as mock_enqueue,
        ):
            triggered = lobby.check_timer()
        assert triggered is True
        assert lobby.status()["triggered"] is True
        mock_enqueue.assert_called_once()

    def test_reset_clears_state(self):
        from server.lobby import Lobby

        lobby = Lobby()
        lobby.join({"name": "P1", "emoji": "A"})
        lobby.reset()
        st = lobby.status()
        assert st["players"] == 0
        assert st["triggered"] is False


# ── 8. TestFillBots ──────────────────────────────────────────────────


class TestFillBots:
    """generate_fill_bots returns valid bot configs."""

    def test_generates_requested_count(self):
        from server.fill_bots import generate_fill_bots

        bots = generate_fill_bots(3, skill_level=0.5)
        assert len(bots) == 3

    def test_bot_config_has_required_fields(self):
        from server.fill_bots import generate_fill_bots

        bots = generate_fill_bots(1, skill_level=0.5)
        bot = bots[0]
        assert "name" in bot
        assert "emoji" in bot
        assert "decide_func" in bot
        assert callable(bot["decide_func"])
        assert "source" in bot

    def test_excludes_used_emojis(self):
        from server.fill_bots import AI_EMOJI_POOL, generate_fill_bots

        used = {AI_EMOJI_POOL[0]}
        bots = generate_fill_bots(2, skill_level=0.5, used_emojis=used)
        emojis = {b["emoji"] for b in bots}
        assert AI_EMOJI_POOL[0] not in emojis


# ── 9. TestPlayerDB ─────────────────────────────────────────────────


class TestPlayerDB:
    """SQLite player registry CRUD and sessions."""

    def test_init_db_creates_tables(self, tmp_path):
        from server.db import init_db

        conn = init_db(str(tmp_path / "test.db"))
        # Verify both tables exist
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        names = {r["name"] for r in tables}
        assert "players" in names
        assert "sessions" in names
        conn.close()

    def test_create_and_get_player(self, tmp_path):
        from server.db import create_player, get_player, init_db

        conn = init_db(str(tmp_path / "test.db"))
        create_player(conn, "p1", "Alice")
        player = get_player(conn, "p1")
        assert player is not None
        assert player["name"] == "Alice"
        conn.close()

    def test_list_players(self, tmp_path):
        from server.db import create_player, init_db, list_players

        conn = init_db(str(tmp_path / "test.db"))
        create_player(conn, "p1", "Alice")
        create_player(conn, "p2", "Bob")
        players = list_players(conn)
        assert len(players) == 2
        conn.close()

    def test_get_nonexistent_player(self, tmp_path):
        from server.db import get_player, init_db

        conn = init_db(str(tmp_path / "test.db"))
        assert get_player(conn, "ghost") is None
        conn.close()

    def test_session_lifecycle(self, tmp_path):
        from server.db import (
            create_player,
            create_session,
            expire_session,
            get_session,
            init_db,
        )

        conn = init_db(str(tmp_path / "test.db"))
        create_player(conn, "p1", "Alice")
        create_session(conn, "tok-1", "p1", "2026-12-31T00:00:00Z")
        sess = get_session(conn, "tok-1")
        assert sess is not None
        assert sess["player_id"] == "p1"

        assert expire_session(conn, "tok-1") is True
        assert get_session(conn, "tok-1") is None
        assert expire_session(conn, "tok-1") is False
        conn.close()
