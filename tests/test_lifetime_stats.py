"""Tests for data.lifetime_stats — per-player lifetime averages."""

import json
import os

import pytest

from data.lifetime_stats import get_lifetime_stats


def _make_match(match_id: int, players: list[dict], winner: str,
                eliminations: list[dict], stats: dict) -> dict:
    """Build a minimal match dict matching the engine's JSON schema."""
    return {
        "match_id": match_id,
        "date": f"2026-01-{match_id:02d}T00:00:00+00:00",
        "grid_size": 11,
        "duration_rounds": 30,
        "players": players,
        "winner": winner,
        "eliminations": eliminations,
        "stats": stats,
        "rounds": [],
    }


def _write_matches(tmp_path, matches: list[dict]) -> str:
    """Write match dicts to JSON files in tmp_path, return dir path."""
    results_dir = str(tmp_path / "results")
    os.makedirs(results_dir, exist_ok=True)
    for m in matches:
        path = os.path.join(results_dir, f"match_{m['match_id']:03d}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(m, f)
    return results_dir


# -- Fixtures for reusable match data --

PLAYER_A = {"emoji": "A", "name": "AlphaBot", "bio": "test", "author": "test"}
PLAYER_B = {"emoji": "B", "name": "BetaBot", "bio": "test", "author": "test"}
PLAYER_C = {"emoji": "C", "name": "GammaBot", "bio": "test", "author": "test"}


def _two_match_fixtures():
    """Return two matches where player A participates in both."""
    match1 = _make_match(
        match_id=1,
        players=[PLAYER_A, PLAYER_B, PLAYER_C],
        winner="A",
        eliminations=[
            {"emoji": "C", "round": 10, "killed_by": "A", "cause": "combat"},
            {"emoji": "B", "round": 20, "killed_by": "A", "cause": "combat"},
        ],
        stats={
            "A": {"kills": 4, "damage_dealt": 200, "damage_taken": 50, "rounds_survived": 30},
            "B": {"kills": 1, "damage_dealt": 80, "damage_taken": 120, "rounds_survived": 20},
            "C": {"kills": 0, "damage_dealt": 30, "damage_taken": 100, "rounds_survived": 10},
        },
    )
    match2 = _make_match(
        match_id=2,
        players=[PLAYER_A, PLAYER_B],
        winner="B",
        eliminations=[
            {"emoji": "A", "round": 25, "killed_by": "B", "cause": "combat"},
        ],
        stats={
            "A": {"kills": 2, "damage_dealt": 100, "damage_taken": 150, "rounds_survived": 25},
            "B": {"kills": 3, "damage_dealt": 150, "damage_taken": 80, "rounds_survived": 30},
        },
    )
    return [match1, match2]


# ---- Cycle 1: Edge cases (empty / missing) ----

class TestEdgeCases:
    def test_nonexistent_results_dir_returns_empty(self):
        result = get_lifetime_stats("/no/such/dir", "A")
        assert result == {}

    def test_player_not_in_any_match_returns_empty(self, tmp_path):
        matches = _two_match_fixtures()
        results_dir = _write_matches(tmp_path, matches)
        result = get_lifetime_stats(results_dir, "Z")
        assert result == {}

    def test_empty_results_dir_returns_empty(self, tmp_path):
        results_dir = str(tmp_path / "results")
        os.makedirs(results_dir)
        result = get_lifetime_stats(results_dir, "A")
        assert result == {}


# ---- Cycle 2: Correct averages ----

class TestAverages:
    def test_kills_averaged_over_matches(self, tmp_path):
        matches = _two_match_fixtures()
        results_dir = _write_matches(tmp_path, matches)
        result = get_lifetime_stats(results_dir, "A")
        # match1: 4 kills, match2: 2 kills -> total 6, matches 2 -> avg 3.0
        assert result["kills"] == pytest.approx(3.0)

    def test_damage_dealt_averaged(self, tmp_path):
        matches = _two_match_fixtures()
        results_dir = _write_matches(tmp_path, matches)
        result = get_lifetime_stats(results_dir, "A")
        # match1: 200, match2: 100 -> total 300, avg 150.0
        assert result["damage_dealt"] == pytest.approx(150.0)

    def test_damage_taken_averaged(self, tmp_path):
        matches = _two_match_fixtures()
        results_dir = _write_matches(tmp_path, matches)
        result = get_lifetime_stats(results_dir, "A")
        # match1: 50, match2: 150 -> total 200, avg 100.0
        assert result["damage_taken"] == pytest.approx(100.0)

    def test_win_rate_kept_as_is(self, tmp_path):
        matches = _two_match_fixtures()
        results_dir = _write_matches(tmp_path, matches)
        result = get_lifetime_stats(results_dir, "A")
        # A won match1, lost match2 -> win_rate = 0.5
        assert result["win_rate"] == pytest.approx(0.5)

    def test_avg_placement_kept_as_is(self, tmp_path):
        matches = _two_match_fixtures()
        results_dir = _write_matches(tmp_path, matches)
        result = get_lifetime_stats(results_dir, "A")
        # match1: 3 players, A won -> placement 1
        # match2: 2 players, A eliminated first -> placement 2
        # avg_placement = (1 + 2) / 2 = 1.5
        assert result["avg_placement"] == pytest.approx(1.5)

    def test_single_match_player(self, tmp_path):
        """Player C only appears in match 1."""
        matches = _two_match_fixtures()
        results_dir = _write_matches(tmp_path, matches)
        result = get_lifetime_stats(results_dir, "C")
        # 1 match: kills=0, damage_dealt=30, damage_taken=100
        assert result["kills"] == pytest.approx(0.0)
        assert result["damage_dealt"] == pytest.approx(30.0)
        assert result["damage_taken"] == pytest.approx(100.0)
