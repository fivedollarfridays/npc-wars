"""Tests for server/routes/stats.py — player stats and leaderboard endpoints."""

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
    {"emoji": "\U0001f916", "name": "Bot1"},  # 🤖
    {"emoji": "\U0001f3af", "name": "Bot2"},  # 🎯
]


@pytest.fixture()
def results_dir(tmp_path):
    """Create a tmp results dir with two match files and wire it into the app."""
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
def empty_results_dir(tmp_path):
    """Create an empty results dir."""
    rdir = str(tmp_path / "results")
    os.makedirs(rdir)
    app.state.results_dir = rdir
    return rdir


@pytest.fixture()
def client():
    return TestClient(app)


# --- Cycle 1: GET /api/stats/{player_id} ---

def test_stats_existing_player(results_dir, client):
    """Existing player returns 200 with averaged lifetime stats."""
    resp = client.get("/api/stats/%F0%9F%A4%96")  # URL-encoded 🤖
    assert resp.status_code == 200
    data = resp.json()
    # 🤖 played 2 matches: kills avg (3+1)/2=2.0, damage_dealt avg (120+80)/2=100.0
    assert data["kills"] == pytest.approx(2.0)
    assert data["damage_dealt"] == pytest.approx(100.0)


def test_stats_nonexistent_player(results_dir, client):
    """Nonexistent player returns 404."""
    resp = client.get("/api/stats/%F0%9F%91%BB")  # 👻 not in any match
    assert resp.status_code == 404
    assert "detail" in resp.json()


# --- Cycle 2: GET /api/leaderboard ---

def test_leaderboard_returns_list(results_dir, client):
    """Leaderboard returns 200 with a list of ranked players."""
    resp = client.get("/api/leaderboard")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    # Default sort_by=wins; both have 1 win so order may vary
    emojis = {entry["emoji"] for entry in data}
    assert "\U0001f916" in emojis
    assert "\U0001f3af" in emojis


def test_leaderboard_empty_results(empty_results_dir, client):
    """Leaderboard with no match files returns empty list."""
    resp = client.get("/api/leaderboard")
    assert resp.status_code == 200
    assert resp.json() == []


def test_leaderboard_sort_by_kills(results_dir, client):
    """Leaderboard with sort_by=kills ranks by total kills descending."""
    resp = client.get("/api/leaderboard?sort_by=kills")
    assert resp.status_code == 200
    data = resp.json()
    # 🤖 has 4 total kills, 🎯 has 3
    assert data[0]["emoji"] == "\U0001f916"
    assert data[0]["kills"] == 4
