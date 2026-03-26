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


def _auth_header(conn) -> dict[str, str]:
    """Create a player and return auth headers."""
    key, _ = _make_player_with_bot(conn, "admin")
    return {"X-API-Key": key}


def test_create_tournament() -> None:
    client = _client()
    conn = app.state.db
    headers = _auth_header(conn)
    resp = client.post("/api/tournament/create", params={"name": "Cup", "size": 8}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "tournament_id" in data
    assert data["name"] == "Cup"
    assert data["size"] == 8


def test_create_tournament_invalid_size() -> None:
    client = _client()
    conn = app.state.db
    headers = _auth_header(conn)
    resp = client.post("/api/tournament/create", params={"name": "Cup", "size": 5}, headers=headers)
    assert resp.status_code == 400


# ── Get tournament ───────────────────────────────────────────────────


def test_get_tournament() -> None:
    client = _client()
    conn = app.state.db
    headers = _auth_header(conn)
    resp = client.post("/api/tournament/create", params={"name": "Cup", "size": 8}, headers=headers)
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
    conn = app.state.db
    headers = _auth_header(conn)
    client.post("/api/tournament/create", params={"name": "A", "size": 8}, headers=headers)
    client.post("/api/tournament/create", params={"name": "B", "size": 8}, headers=headers)
    resp = client.get("/api/tournaments")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tournaments"]) == 2


# ── Join tournament ──────────────────────────────────────────────────


def test_join_tournament() -> None:
    client = _client()
    conn = app.state.db
    key, bot_id = _make_player_with_bot(conn, "p1")
    resp = client.post(
        "/api/tournament/create",
        params={"name": "Cup", "size": 8},
        headers={"X-API-Key": key},
    )
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
    admin_key, _ = _make_player_with_bot(conn, "admin_seed")
    resp = client.post(
        "/api/tournament/create",
        params={"name": "Cup", "size": 8},
        headers={"X-API-Key": admin_key},
    )
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


def _setup_full_tournament(client: TestClient, conn) -> tuple[int, str]:
    """Create and fill a tournament. Returns (tournament_id, admin_api_key)."""
    admin_key, _ = _make_player_with_bot(conn, "admin_rr")
    resp = client.post(
        "/api/tournament/create",
        params={"name": "Cup", "size": 8},
        headers={"X-API-Key": admin_key},
    )
    tid = resp.json()["tournament_id"]
    for i in range(8):
        key, bot_id = _make_player_with_bot(conn, f"r{i}")
        client.post(
            f"/api/tournament/{tid}/join",
            params={"bot_id": bot_id},
            headers={"X-API-Key": key},
        )
    return tid, admin_key


@patch("server.tournament_runner.run_match", side_effect=_fake_run_match)
def test_run_round(mock_run: object) -> None:
    client = _client()
    conn = app.state.db
    tid, admin_key = _setup_full_tournament(client, conn)
    resp = client.post(
        f"/api/tournament/{tid}/run-round",
        headers={"X-API-Key": admin_key},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 2


# ── Results ──────────────────────────────────────────────────────────


@patch("server.tournament_runner.run_match", side_effect=_fake_run_match)
def test_get_results(mock_run: object) -> None:
    client = _client()
    conn = app.state.db
    tid, admin_key = _setup_full_tournament(client, conn)
    headers = {"X-API-Key": admin_key}
    client.post(f"/api/tournament/{tid}/run-round", headers=headers)
    client.post(f"/api/tournament/{tid}/run-round", headers=headers)
    resp = client.get(f"/api/tournament/{tid}/results")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "complete"
    assert data["winner"] is not None
