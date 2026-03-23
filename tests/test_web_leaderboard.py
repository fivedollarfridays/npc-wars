"""Tests for web leaderboard page routes and match history API."""

import json
import os

import pytest
from fastapi.testclient import TestClient

from server.app import app


def _make_match(match_id: int, winner: str, players: list[dict],
                stats: dict, eliminations: list) -> dict:
    """Build a minimal match dict for testing."""
    return {
        "match_id": match_id,
        "date": "2026-03-16",
        "winner": winner,
        "duration_rounds": 10,
        "players": players,
        "stats": stats,
        "eliminations": eliminations,
    }


PLAYERS_AB = [
    {"emoji": "\U0001f916", "name": "Bot1"},
    {"emoji": "\U0001f3af", "name": "Bot2"},
]


@pytest.fixture()
def results_dir(tmp_path):
    """Create a tmp results dir with match files and wire it into the app."""
    match1 = _make_match(
        match_id=1,
        winner="\U0001f916",
        players=PLAYERS_AB,
        stats={
            "\U0001f916": {"kills": 3, "damage_dealt": 120, "damage_taken": 40},
            "\U0001f3af": {"kills": 1, "damage_dealt": 40, "damage_taken": 120},
        },
        eliminations=[{"emoji": "\U0001f3af", "round": 10}],
    )
    match2 = _make_match(
        match_id=2,
        winner="\U0001f3af",
        players=PLAYERS_AB,
        stats={
            "\U0001f916": {"kills": 1, "damage_dealt": 80, "damage_taken": 60},
            "\U0001f3af": {"kills": 2, "damage_dealt": 60, "damage_taken": 80},
        },
        eliminations=[{"emoji": "\U0001f916", "round": 8}],
    )
    rdir = str(tmp_path / "results")
    os.makedirs(rdir)
    for m in (match1, match2):
        path = os.path.join(rdir, f"match_{m['match_id']:03d}.json")
        with open(path, "w") as f:
            json.dump(m, f)

    app.state.results_dir = rdir
    return rdir


@pytest.fixture()
def client():
    return TestClient(app)


# --- Cycle 1: HTML page routes ---

def test_leaderboard_page_returns_html(client):
    """GET /leaderboard returns 200 with HTML content."""
    resp = client.get("/leaderboard")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "LEADERBOARD" in resp.text


def test_profile_page_returns_html(client):
    """GET /profile/test-player returns 200 with HTML content."""
    resp = client.get("/profile/test-player")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "PROFILE" in resp.text


# --- Cycle 2: Match history API ---

def test_matches_api_returns_list(results_dir, client):
    """GET /api/matches/{emoji} returns list of match entries for that player."""
    resp = client.get("/api/matches/%F0%9F%A4%96")  # URL-encoded robot emoji
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    # Each entry has match_id and winner
    assert data[0]["match_id"] in (1, 2)
    assert "winner" in data[0]


def test_matches_api_unknown_player(results_dir, client):
    """GET /api/matches/{emoji} for unknown player returns empty list."""
    resp = client.get("/api/matches/%F0%9F%91%BB")  # ghost emoji, not in matches
    assert resp.status_code == 200
    assert resp.json() == []


def test_matches_api_has_duration(results_dir, client):
    """Match entries include duration_rounds field."""
    resp = client.get("/api/matches/%F0%9F%A4%96")
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["duration_rounds"] == 10
