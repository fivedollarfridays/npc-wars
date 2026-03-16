"""Tests for diff data injection into match JSON."""

import json
import os
from data.stat_diff import inject_diff_data


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


PLAYER_A = {"emoji": "A", "name": "AlphaBot", "bio": "test", "author": "test"}
PLAYER_B = {"emoji": "B", "name": "BetaBot", "bio": "test", "author": "test"}


# ---- Cycle 1: Basic injection ----

class TestInjectDiffData:
    """inject_diff_data adds a 'diff' key with per-player diff entries."""

    def test_adds_diff_key(self, tmp_path):
        """After injection, match_data has a 'diff' key."""
        history_match = _make_match(
            match_id=1, players=[PLAYER_A, PLAYER_B], winner="A",
            eliminations=[], stats={
                "A": {"kills": 4, "damage_dealt": 200, "damage_taken": 50},
                "B": {"kills": 1, "damage_dealt": 80, "damage_taken": 120},
            },
        )
        results_dir = _write_matches(tmp_path, [history_match])

        current_match = _make_match(
            match_id=2, players=[PLAYER_A, PLAYER_B], winner="B",
            eliminations=[], stats={
                "A": {"kills": 6, "damage_dealt": 300, "damage_taken": 40},
                "B": {"kills": 3, "damage_dealt": 100, "damage_taken": 80},
            },
        )
        result = inject_diff_data(current_match, results_dir)
        assert "diff" in result
        assert "A" in result["diff"]
        assert "B" in result["diff"]

    def test_diff_contains_classification_delta_percentage(self, tmp_path):
        """Each player diff entry has classification, delta, percentage per stat."""
        history_match = _make_match(
            match_id=1, players=[PLAYER_A], winner="A",
            eliminations=[], stats={
                "A": {"kills": 4, "damage_dealt": 200, "damage_taken": 50},
            },
        )
        results_dir = _write_matches(tmp_path, [history_match])

        current_match = _make_match(
            match_id=2, players=[PLAYER_A], winner="A",
            eliminations=[], stats={
                "A": {"kills": 6, "damage_dealt": 150, "damage_taken": 50},
            },
        )
        result = inject_diff_data(current_match, results_dir)
        diff_a = result["diff"]["A"]
        assert diff_a["kills"]["classification"] == "improved"
        assert diff_a["kills"]["delta"] == 2.0
        assert diff_a["damage_dealt"]["classification"] == "regressed"

    def test_returns_modified_match_data(self, tmp_path):
        """inject_diff_data returns the same dict (mutated in place)."""
        history_match = _make_match(
            match_id=1, players=[PLAYER_A], winner="A",
            eliminations=[], stats={"A": {"kills": 2}},
        )
        results_dir = _write_matches(tmp_path, [history_match])
        current_match = _make_match(
            match_id=2, players=[PLAYER_A], winner="A",
            eliminations=[], stats={"A": {"kills": 5}},
        )
        result = inject_diff_data(current_match, results_dir)
        assert result is current_match


# ---- Cycle 2: First match (no history) ----

class TestFirstMatchDiff:
    """When a player has no history, diff should include first_match sentinel."""

    def test_first_match_sentinel(self, tmp_path):
        """Player with no history gets first_match=True in diff."""
        results_dir = str(tmp_path / "results")
        os.makedirs(results_dir, exist_ok=True)
        # No history files -- empty dir

        current_match = _make_match(
            match_id=1, players=[PLAYER_A], winner="A",
            eliminations=[], stats={"A": {"kills": 5, "damage_dealt": 100}},
        )
        result = inject_diff_data(current_match, results_dir)
        assert result["diff"]["A"]["first_match"] is True


# ---- Cycle 3: Graceful handling of missing results_dir ----

class TestGracefulHandling:
    """inject_diff_data handles edge cases without crashing."""

    def test_missing_results_dir(self):
        """Non-existent results dir still produces diffs (first_match)."""
        current_match = _make_match(
            match_id=1, players=[PLAYER_A], winner="A",
            eliminations=[], stats={"A": {"kills": 3}},
        )
        result = inject_diff_data(current_match, "/no/such/dir")
        assert "diff" in result
        assert result["diff"]["A"]["first_match"] is True

    def test_empty_stats_dict(self, tmp_path):
        """Match with empty stats dict gets empty diff."""
        results_dir = str(tmp_path / "results")
        os.makedirs(results_dir, exist_ok=True)
        current_match = _make_match(
            match_id=1, players=[PLAYER_A], winner="A",
            eliminations=[], stats={},
        )
        result = inject_diff_data(current_match, results_dir)
        assert result["diff"] == {}
