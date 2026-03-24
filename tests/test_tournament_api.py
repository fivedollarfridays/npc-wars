"""Tests for tournament API endpoints."""

from __future__ import annotations

import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from server.app import app
from server.db import create_api_key, create_player, init_db, store_bot
from server.tournament_db import get_tournament


def _client() -> TestClient:
    """Create a test client with fresh in-memory DB."""
    app.state.db = init_db(":memory:")
    return TestClient(app)


def _make_player_with_bot(conn, pid: str = "p1") -> tuple[str, int]:
    """Create a player with an API key and a bot. Returns (api_key, bot_id)."""
    create_player(conn, pid, f"Player {pid}")
    key = create_api_key(conn, pid)
    bot_id = store_bot(
        conn, pid, f"Bot {pid}", "B",
        "BOT_NAME='TestBot'\ndef setup(state): pass\ndef take_turn(state): return 'north'"
    )
    return key, bot_id


# ── Create tournament ────────────────────────────────────────────────


def test_create_tournament() -> None:
    client = _client()
    resp = client.post("/api/tournament/create", params={"name": "Cup", "size": 8})
    assert resp.status_code == 200
    data = resp.json()
    assert "tournament_id" in data
    assert data["name"] == "Cup"
    assert data["size"] == 8


def test_create_tournament_invalid_size() -> None:
    client = _client()
    resp = client.post("/api/tournament/create", params={"name": "Cup", "size": 5})
    assert resp.status_code == 400


# ── Get tournament ───────────────────────────────────────────────────


def test_get_tournament() -> None:
    client = _client()
    resp = client.post("/api/tournament/create", params={"name": "Cup", "size": 8})
    tid = resp.json()["tournament_id"]
    resp = client.get(f"/api/tournament/{tid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Cup"
    assert data["status"] == "open"


def test_get_tournament_not_found() -> None:
    client = _client()
    resp = client.get("/api/tournament/999")
    assert resp.status_code == 404


# ── List tournaments ─────────────────────────────────────────────────


def test_list_tournaments() -> None:
    client = _client()
    client.post("/api/tournament/create", params={"name": "A", "size": 8})
    client.post("/api/tournament/create", params={"name": "B", "size": 8})
    resp = client.get("/api/tournaments")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tournaments"]) == 2


# ── Join tournament ──────────────────────────────────────────────────


def test_join_tournament() -> None:
    client = _client()
    conn = app.state.db
    key, bot_id = _make_player_with_bot(conn, "p1")
    resp = client.post("/api/tournament/create", params={"name": "Cup", "size": 8})
    tid = resp.json()["tournament_id"]
    resp = client.post(
        f"/api/tournament/{tid}/join",
        params={"bot_id": bot_id},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200
    assert resp.json()["joined"] is True


def test_join_tournament_auto_seeds_when_full() -> None:
    client = _client()
    conn = app.state.db
    resp = client.post("/api/tournament/create", params={"name": "Cup", "size": 8})
    tid = resp.json()["tournament_id"]
    for i in range(8):
        key, bot_id = _make_player_with_bot(conn, f"p{i}")
        client.post(
            f"/api/tournament/{tid}/join",
            params={"bot_id": bot_id},
            headers={"X-API-Key": key},
        )
    row = get_tournament(conn, tid)
    assert row is not None
    data = json.loads(row["bracket_json"])
    assert data["status"] == "running"


def test_join_tournament_not_found() -> None:
    client = _client()
    conn = app.state.db
    key, bot_id = _make_player_with_bot(conn, "p1")
    resp = client.post(
        "/api/tournament/999/join",
        params={"bot_id": bot_id},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 404


# ── Run round ────────────────────────────────────────────────────────


def _fake_run_match(bot_configs, match_id=1, seed=None, map_name="arena"):
    """Fake run_match for API tests."""
    names = [c["name"] for c in bot_configs]
    pids = [c["player_id"] for c in bot_configs]
    return {
        "match_id": match_id,
        "winner": names[0],
        "placements": names,
        "players": [
            {"name": n, "alive": i == 0, "player_id": pid}
            for i, (n, pid) in enumerate(zip(names, pids))
        ],
    }


def _setup_full_tournament(client: TestClient, conn) -> int:
    """Create and fill a tournament. Returns tournament_id."""
    resp = client.post("/api/tournament/create", params={"name": "Cup", "size": 8})
    tid = resp.json()["tournament_id"]
    for i in range(8):
        key, bot_id = _make_player_with_bot(conn, f"r{i}")
        client.post(
            f"/api/tournament/{tid}/join",
            params={"bot_id": bot_id},
            headers={"X-API-Key": key},
        )
    return tid


@patch("server.tournament_runner.run_match", side_effect=_fake_run_match)
def test_run_round(mock_run: object) -> None:
    client = _client()
    conn = app.state.db
    tid = _setup_full_tournament(client, conn)
    resp = client.post(f"/api/tournament/{tid}/run-round")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 2


# ── Results ──────────────────────────────────────────────────────────


@patch("server.tournament_runner.run_match", side_effect=_fake_run_match)
def test_get_results(mock_run: object) -> None:
    client = _client()
    conn = app.state.db
    tid = _setup_full_tournament(client, conn)
    client.post(f"/api/tournament/{tid}/run-round")
    client.post(f"/api/tournament/{tid}/run-round")
    resp = client.get(f"/api/tournament/{tid}/results")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "complete"
    assert data["winner"] is not None
