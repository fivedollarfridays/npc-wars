"""Tests for tournament automated match runner."""

from __future__ import annotations

import json
from unittest.mock import patch

from server.db import init_db, create_player, store_bot
from server.tournament import Tournament
from server.tournament_db import create_tournament, get_tournament, update_tournament
from server.tournament_runner import run_tournament_round


def _setup_tournament(size: int = 8) -> tuple:
    """Create a DB, tournament, and players with bots. Returns (conn, tid)."""
    conn = init_db(":memory:")
    tid = create_tournament(conn, "Test Cup", size, "arena")

    t = Tournament("Test Cup", size, seed=42)
    for i in range(size):
        pid = f"player_{i}"
        create_player(conn, pid, f"Player {i}")
        store_bot(conn, pid, f"Bot {i}", "B", f"BOT_NAME='Bot {i}'\ndef setup(state): pass\ndef take_turn(state): return 'north'")
        t.add_player(pid)

    t.seed_bracket()
    update_tournament(conn, tid, json.dumps(t.to_dict()), t.status, t.winner)
    return conn, tid


def _fake_run_match(bot_configs, match_id=1, seed=None, map_name="arena"):
    """Fake run_match that returns deterministic results.

    Uses player_id from bot_configs so the tournament can map back.
    """
    names = [c["name"] for c in bot_configs]
    player_ids = [c["player_id"] for c in bot_configs]
    return {
        "match_id": match_id,
        "winner": names[0],
        "placements": names,
        "players": [
            {"name": n, "alive": i == 0, "player_id": pid}
            for i, (n, pid) in enumerate(zip(names, player_ids))
        ],
    }


@patch("server.tournament_runner.run_match", side_effect=_fake_run_match)
def test_run_round_executes_pending_matches(mock_run: object) -> None:
    conn, tid = _setup_tournament(8)
    results = run_tournament_round(conn, tid)
    # 8 players in groups of 4 = 2 matches in round 1
    assert len(results) == 2


@patch("server.tournament_runner.run_match", side_effect=_fake_run_match)
def test_run_round_updates_db(mock_run: object) -> None:
    conn, tid = _setup_tournament(8)
    run_tournament_round(conn, tid)
    row = get_tournament(conn, tid)
    assert row is not None
    data = json.loads(row["bracket_json"])
    # Round 1 results should be recorded
    assert data["rounds"][0][0]["results"] is not None


@patch("server.tournament_runner.run_match", side_effect=_fake_run_match)
def test_run_round_advances_bracket(mock_run: object) -> None:
    conn, tid = _setup_tournament(8)
    run_tournament_round(conn, tid)
    row = get_tournament(conn, tid)
    assert row is not None
    data = json.loads(row["bracket_json"])
    # After round 1 completes, round 2 (final) should be created
    assert len(data["rounds"]) == 2


@patch("server.tournament_runner.run_match", side_effect=_fake_run_match)
def test_run_round_no_pending_returns_empty(mock_run: object) -> None:
    conn, tid = _setup_tournament(8)
    run_tournament_round(conn, tid)  # Round 1
    run_tournament_round(conn, tid)  # Round 2 (final)
    results = run_tournament_round(conn, tid)  # No more matches
    assert results == []


@patch("server.tournament_runner.run_match", side_effect=_fake_run_match)
def test_full_tournament_completes(mock_run: object) -> None:
    conn, tid = _setup_tournament(8)
    run_tournament_round(conn, tid)  # Round 1
    run_tournament_round(conn, tid)  # Final
    row = get_tournament(conn, tid)
    assert row is not None
    assert row["status"] == "complete"
    assert row["winner"] is not None
