"""Tests for engine/match_writer.py — JSON output structure and file creation."""

import json
import os

from engine.match_writer import build_match_data, write_match


def _sample_match_data(match_id=1):
    return build_match_data(
        match_id=match_id,
        grid_size=11,
        players=[{"emoji": "🤖", "name": "Bot", "bio": "", "author": "test"}],
        rounds=[{
            "round": 1,
            "storm_border": 0,
            "positions": [{"emoji": "🤖", "x": 5, "y": 5, "hp": 100, "energy": 95, "action": "move north", "alive": True}],
            "events": [],
        }],
        eliminations=[],
        winner_emoji="🤖",
        stats={"🤖": {"kills": 0, "damage_dealt": 0, "damage_taken": 0, "rounds_survived": 1}},
        duration_rounds=1,
    )


class TestBuildMatchData:
    def test_required_top_level_keys(self):
        data = _sample_match_data()
        expected = {
            "match_id", "date", "grid_size", "players", "rounds",
            "eliminations", "winner", "stats", "duration_rounds", "carryover",
        }
        assert set(data.keys()) == expected

    def test_match_id_set(self):
        assert _sample_match_data(match_id=42)["match_id"] == 42

    def test_date_is_iso_format(self):
        data = _sample_match_data()
        assert "T" in data["date"]  # ISO format has T separator

    def test_grid_size_value(self):
        assert _sample_match_data()["grid_size"] == 11

    def test_players_list(self):
        data = _sample_match_data()
        assert len(data["players"]) == 1
        assert data["players"][0]["emoji"] == "🤖"

    def test_winner_set(self):
        assert _sample_match_data()["winner"] == "🤖"

    def test_duration_rounds(self):
        assert _sample_match_data()["duration_rounds"] == 1


class TestWriteMatch:
    def test_creates_file(self, tmp_path):
        data = _sample_match_data(match_id=1)
        filepath = write_match(data, str(tmp_path))
        assert os.path.exists(filepath)

    def test_filename_format(self, tmp_path):
        data = _sample_match_data(match_id=7)
        filepath = write_match(data, str(tmp_path))
        assert filepath.endswith("match_007.json")

    def test_valid_json(self, tmp_path):
        data = _sample_match_data()
        filepath = write_match(data, str(tmp_path))
        with open(filepath) as f:
            loaded = json.load(f)
        assert loaded["match_id"] == 1

    def test_creates_results_dir(self, tmp_path):
        subdir = str(tmp_path / "nested" / "results")
        data = _sample_match_data()
        filepath = write_match(data, subdir)
        assert os.path.exists(filepath)

    def test_round_structure_preserved(self, tmp_path):
        data = _sample_match_data()
        filepath = write_match(data, str(tmp_path))
        with open(filepath) as f:
            loaded = json.load(f)
        rnd = loaded["rounds"][0]
        assert set(rnd.keys()) == {"round", "storm_border", "positions", "events"}

    def test_position_structure_preserved(self, tmp_path):
        data = _sample_match_data()
        filepath = write_match(data, str(tmp_path))
        with open(filepath) as f:
            loaded = json.load(f)
        pos = loaded["rounds"][0]["positions"][0]
        assert set(pos.keys()) == {"emoji", "x", "y", "hp", "energy", "action", "alive"}


class TestBroadcastInbox:
    """BC2.4: optional broadcast_inbox param copies match JSON to broadcast inbox dir."""

    def test_no_broadcast_inbox_writes_only_results(self, tmp_path):
        results = tmp_path / "results"
        data = _sample_match_data(match_id=3)
        filepath = write_match(data, str(results))
        assert os.path.exists(filepath)
        # No other directories created
        assert sorted(p.name for p in tmp_path.iterdir()) == ["results"]

    def test_broadcast_inbox_none_preserves_prior_behavior(self, tmp_path):
        results = tmp_path / "results"
        data = _sample_match_data(match_id=5)
        filepath = write_match(data, str(results), broadcast_inbox=None)
        assert os.path.exists(filepath)
        assert filepath.endswith("match_005.json")

    def test_broadcast_inbox_writes_duplicate(self, tmp_path):
        results = tmp_path / "results"
        inbox = tmp_path / "inbox"
        data = _sample_match_data(match_id=9)
        filepath = write_match(data, str(results), broadcast_inbox=str(inbox))
        inbox_file = inbox / "match_009.json"
        assert os.path.exists(filepath)
        assert inbox_file.exists()
        with open(inbox_file) as f:
            loaded = json.load(f)
        assert loaded["match_id"] == 9

    def test_broadcast_inbox_auto_creates_directory(self, tmp_path):
        results = tmp_path / "results"
        inbox = tmp_path / "nested" / "missing" / "inbox"
        assert not inbox.exists()
        data = _sample_match_data(match_id=11)
        write_match(data, str(results), broadcast_inbox=str(inbox))
        assert inbox.is_dir()
        assert (inbox / "match_011.json").exists()

    def test_broadcast_inbox_contents_match_results(self, tmp_path):
        results = tmp_path / "results"
        inbox = tmp_path / "inbox"
        data = _sample_match_data(match_id=7)
        filepath = write_match(data, str(results), broadcast_inbox=str(inbox))
        with open(filepath) as f:
            primary = json.load(f)
        with open(inbox / "match_007.json") as f:
            copied = json.load(f)
        assert primary == copied

    def test_return_value_is_results_path(self, tmp_path):
        """Returned path remains the results path, not the inbox path."""
        results = tmp_path / "results"
        inbox = tmp_path / "inbox"
        data = _sample_match_data(match_id=1)
        filepath = write_match(data, str(results), broadcast_inbox=str(inbox))
        assert filepath.startswith(str(results))
