"""Tests for data/rivalry_db.py — I/O wrapper for rivalry computation."""

import json
import os
import tempfile

from data.rivalry_db import compute_rivalry


def _write_match(d, match):
    path = os.path.join(d, f"match_{match['match_id']:03d}.json")
    with open(path, "w") as f:
        json.dump(match, f)


def _make_match(match_id, winner, players):
    return {
        "match_id": match_id,
        "date": f"2026-01-{match_id:02d}T00:00:00",
        "winner": winner,
        "players": [{"emoji": e} for e in players],
        "eliminations": [],
        "stats": {e: {"kills": 0, "damage_dealt": 0, "damage_taken": 0,
                        "rounds_survived": 5} for e in players},
        "duration_rounds": 10,
    }


class TestComputeRivalry:
    def test_returns_full_rivalry_dict(self):
        with tempfile.TemporaryDirectory() as d:
            _write_match(d, _make_match(1, "\U0001f916", ["\U0001f916", "\U0001f3af"]))
            _write_match(d, _make_match(2, "\U0001f3af", ["\U0001f916", "\U0001f3af"]))
            result = compute_rivalry("\U0001f916", "\U0001f3af", d)

        assert "wins_a" in result
        assert "wins_b" in result
        assert "score" in result
        assert "trend" in result
        assert 0 <= result["score"] <= 100

    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as d:
            result = compute_rivalry("\U0001f916", "\U0001f3af", d)
        assert result["matches"] == 0
        assert result["score"] == 50

    def test_nonexistent_dir(self):
        result = compute_rivalry("\U0001f916", "\U0001f3af", "/tmp/no_such_dir_12345")
        assert result["matches"] == 0
