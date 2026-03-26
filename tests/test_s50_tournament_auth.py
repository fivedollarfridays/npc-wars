"""Tests for S50: tournament auth hardening + bot source size cap."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from server.app import app
from server.db import create_api_key, create_player, init_db, store_bot


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
        "BOT_NAME='TestBot'\ndef setup(state): pass\ndef take_turn(state): return 'north'",
    )
    return key, bot_id


def _fake_run_match(bot_configs, match_id=1, seed=None, map_name="arena"):
    """Fake run_match for tournament round tests."""
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


def _setup_full_tournament(client: TestClient, conn, key: str) -> int:
    """Create and fill a tournament (auth required). Returns tournament_id."""
    resp = client.post(
        "/api/tournament/create",
        params={"name": "Cup", "size": 8},
        headers={"X-API-Key": key},
    )
    tid = resp.json()["tournament_id"]
    for i in range(8):
        k, bot_id = _make_player_with_bot(conn, f"s{i}")
        client.post(
            f"/api/tournament/{tid}/join",
            params={"bot_id": bot_id},
            headers={"X-API-Key": k},
        )
    return tid


# ── Create tournament auth ──────────────────────────────────────────


def test_create_tournament_requires_auth() -> None:
    """POST /api/tournament/create without X-API-Key returns 401."""
    client = _client()
    resp = client.post("/api/tournament/create", params={"name": "Cup", "size": 8})
    assert resp.status_code == 401


def test_create_tournament_with_auth() -> None:
    """POST /api/tournament/create with valid key succeeds."""
    client = _client()
    conn = app.state.db
    key, _ = _make_player_with_bot(conn, "auth1")
    resp = client.post(
        "/api/tournament/create",
        params={"name": "Cup", "size": 8},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200
    assert "tournament_id" in resp.json()


# ── Run round auth ──────────────────────────────────────────────────


def test_run_round_requires_auth() -> None:
    """POST /api/tournament/{id}/run-round without key returns 401."""
    client = _client()
    conn = app.state.db
    key, _ = _make_player_with_bot(conn, "auth2")
    # Create tournament with auth so it exists
    resp = client.post(
        "/api/tournament/create",
        params={"name": "Cup", "size": 8},
        headers={"X-API-Key": key},
    )
    tid = resp.json()["tournament_id"]
    # Try run-round without auth
    resp = client.post(f"/api/tournament/{tid}/run-round")
    assert resp.status_code == 401


@patch("server.tournament_runner.run_match", side_effect=_fake_run_match)
def test_run_round_with_auth(mock_run: object) -> None:
    """POST /api/tournament/{id}/run-round with valid key succeeds."""
    client = _client()
    conn = app.state.db
    key, _ = _make_player_with_bot(conn, "auth3")
    tid = _setup_full_tournament(client, conn, key)
    resp = client.post(
        f"/api/tournament/{tid}/run-round",
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200
    assert "results" in resp.json()


# ── Public endpoints stay open ──────────────────────────────────────


def test_get_tournament_no_auth_ok() -> None:
    """GET /api/tournament/{id} without key returns 200."""
    client = _client()
    conn = app.state.db
    key, _ = _make_player_with_bot(conn, "pub1")
    resp = client.post(
        "/api/tournament/create",
        params={"name": "Cup", "size": 8},
        headers={"X-API-Key": key},
    )
    tid = resp.json()["tournament_id"]
    resp = client.get(f"/api/tournament/{tid}")
    assert resp.status_code == 200


def test_list_tournaments_no_auth_ok() -> None:
    """GET /api/tournaments without key returns 200."""
    client = _client()
    resp = client.get("/api/tournaments")
    assert resp.status_code == 200


# ── Bot source size cap ─────────────────────────────────────────────


def test_submit_bot_source_too_large() -> None:
    """Source exceeding 50K chars returns 422."""
    client = _client()
    oversized = "x" * 50_001
    resp = client.post("/api/submit-bot", json={"source": oversized})
    assert resp.status_code == 422


def test_submit_bot_source_at_limit() -> None:
    """Source at exactly 50K chars is accepted (not rejected by size cap)."""
    client = _client()
    # Build valid Python source padded to exactly 50K
    base = "def decide(me, enemies, storm): return {'move': 'north', 'action': 'none'}\n"
    pad = "# " + "x" * (50_000 - len(base) - 3) + "\n"
    source = base + pad
    assert len(source) == 50_000
    resp = client.post("/api/submit-bot", json={"source": source})
    # Should NOT be 422 — size cap allows exactly 50K
    assert resp.status_code != 422
