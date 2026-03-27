"""Tests for leaderboard rival-tier badges (T55.3)."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.db import init_db, create_player, store_bot
from server.rival_db import ensure_rival_progress, record_rival_attempt, WINS_TO_ADVANCE


@pytest.fixture(autouse=True)
def setup_db():
    old_db = getattr(app.state, "db", None)
    app.state.db = init_db(":memory:")
    yield
    app.state.db = old_db


client = TestClient(app)


# ── Cycle 1: emoji-to-rival lookup helper ─────────────────────────────


def test_emoji_rival_map_empty_db():
    """No bots registered -> empty map."""
    from server.routes.stats import _emoji_rival_map

    result = _emoji_rival_map(app.state.db, ["🔥", "💀"])
    assert result == {"🔥": {"rival_tier": 0, "graduated": False},
                      "💀": {"rival_tier": 0, "graduated": False}}


def test_emoji_rival_map_with_registered_bot():
    """Bot with rival progress -> tier from DB."""
    from server.routes.stats import _emoji_rival_map

    db = app.state.db
    create_player(db, "p1", "Player1")
    store_bot(db, "p1", "Bot1", "🔥", "pass")
    ensure_rival_progress(db, "p1")
    for _ in range(WINS_TO_ADVANCE):
        record_rival_attempt(db, "p1", won=True)

    result = _emoji_rival_map(db, ["🔥"])
    assert result["🔥"]["rival_tier"] == 2
    assert result["🔥"]["graduated"] is False


def test_emoji_rival_map_graduated():
    """Bot whose player graduated -> graduated=True."""
    from server.routes.stats import _emoji_rival_map
    from server.rival_db import MAX_RIVAL_TIER

    db = app.state.db
    create_player(db, "p1", "Player1")
    store_bot(db, "p1", "Bot1", "⚡", "pass")
    ensure_rival_progress(db, "p1")
    for _ in range(MAX_RIVAL_TIER * WINS_TO_ADVANCE):
        record_rival_attempt(db, "p1", won=True)

    result = _emoji_rival_map(db, ["⚡"])
    assert result["⚡"]["graduated"] is True


# ── Cycle 2: leaderboard API includes rival fields ────────────────────


@pytest.fixture()
def results_with_match(tmp_path):
    """Create a results dir with one match so leaderboard returns data."""
    match = {
        "match_id": 1,
        "players": [
            {"emoji": "🔥", "name": "Bot1"},
            {"emoji": "💀", "name": "Bot2"},
        ],
        "winner": "🔥",
        "eliminations": [{"emoji": "💀", "round": 5}],
        "stats": {
            "🔥": {"kills": 1, "damage_dealt": 50, "damage_taken": 10},
            "💀": {"kills": 0, "damage_dealt": 10, "damage_taken": 50},
        },
    }
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    (results_dir / "match_1.json").write_text(json.dumps(match))
    old_dir = app.state.results_dir
    app.state.results_dir = str(results_dir)
    yield
    app.state.results_dir = old_dir


def test_leaderboard_api_has_rival_fields(results_with_match):
    """Each entry in /api/leaderboard should have rival_tier and graduated."""
    resp = client.get("/api/leaderboard?sort_by=wins")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    for entry in data:
        assert "rival_tier" in entry
        assert "graduated" in entry


def test_leaderboard_api_reflects_tier(results_with_match):
    """A registered bot's rival tier shows in the API."""
    db = app.state.db
    create_player(db, "p1", "Player1")
    store_bot(db, "p1", "Bot1", "🔥", "pass")
    ensure_rival_progress(db, "p1")
    for _ in range(WINS_TO_ADVANCE):
        record_rival_attempt(db, "p1", won=True)

    resp = client.get("/api/leaderboard?sort_by=wins")
    data = resp.json()
    fire_entry = next(e for e in data if e["emoji"] == "🔥")
    assert fire_entry["rival_tier"] == 2


# ── Cycle 3: HTML has badge rendering ─────────────────────────────────


def test_leaderboard_html_has_badge_rendering():
    html = Path("server/static/leaderboard.html").read_text()
    assert "rival_tier" in html or "badge" in html.lower() or "tier" in html.lower()


def test_leaderboard_html_has_trophy():
    html = Path("server/static/leaderboard.html").read_text()
    assert "🏆" in html or "trophy" in html.lower()


def test_leaderboard_page_loads():
    resp = client.get("/leaderboard")
    assert resp.status_code == 200
