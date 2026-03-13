"""Tests for data/match_history.py — indexing, querying, pagination, filtering."""

import json

import pytest

from data.match_history import (
    get_latest_match,
    get_match,
    index_matches,
    list_matches,
)


# --- Helpers ---


def _write_match(tmp_path, match_id, winner="🅰️", date="2026-01-01T00:00:00+00:00",
                 players=None, duration=10):
    if players is None:
        players = [
            {"emoji": "🅰️", "name": "A", "bio": "", "author": "t"},
            {"emoji": "🅱️", "name": "B", "bio": "", "author": "t"},
        ]
    data = {
        "match_id": match_id,
        "date": date,
        "grid_size": 10,
        "players": players,
        "rounds": [],
        "eliminations": [],
        "winner": winner,
        "stats": {},
        "duration_rounds": duration,
    }
    path = tmp_path / f"match_{match_id:03d}.json"
    path.write_text(json.dumps(data))
    return data


# --- index_matches ---


class TestIndexMatches:
    def test_empty_dir_returns_empty(self, tmp_path):
        assert index_matches(str(tmp_path)) == []

    def test_indexes_single_match(self, tmp_path):
        _write_match(tmp_path, 1)
        index = index_matches(str(tmp_path))
        assert len(index) == 1

    def test_index_entry_has_required_fields(self, tmp_path):
        _write_match(tmp_path, 1, winner="🅰️", date="2026-01-15T12:00:00+00:00", duration=42)
        entry = index_matches(str(tmp_path))[0]
        assert entry["match_id"] == 1
        assert entry["date"] == "2026-01-15T12:00:00+00:00"
        assert entry["winner"] == "🅰️"
        assert entry["player_count"] == 2
        assert entry["duration_rounds"] == 42

    def test_indexes_multiple_matches_sorted_by_id(self, tmp_path):
        _write_match(tmp_path, 3)
        _write_match(tmp_path, 1)
        _write_match(tmp_path, 2)
        index = index_matches(str(tmp_path))
        assert [e["match_id"] for e in index] == [1, 2, 3]

    def test_skips_non_json_files(self, tmp_path):
        _write_match(tmp_path, 1)
        (tmp_path / "notes.txt").write_text("ignore me")
        assert len(index_matches(str(tmp_path))) == 1

    def test_missing_dir_returns_empty(self, tmp_path):
        assert index_matches(str(tmp_path / "nonexistent")) == []


# --- get_match ---


class TestGetMatch:
    def test_get_existing_match(self, tmp_path):
        _write_match(tmp_path, 5, winner="🅱️")
        match = get_match(str(tmp_path), 5)
        assert match["match_id"] == 5
        assert match["winner"] == "🅱️"

    def test_get_nonexistent_match_returns_none(self, tmp_path):
        assert get_match(str(tmp_path), 99) is None


# --- list_matches ---


class TestListMatches:
    def test_list_all(self, tmp_path):
        for i in range(1, 4):
            _write_match(tmp_path, i)
        result = list_matches(str(tmp_path))
        assert len(result) == 3

    def test_limit(self, tmp_path):
        for i in range(1, 6):
            _write_match(tmp_path, i)
        result = list_matches(str(tmp_path), limit=3)
        assert len(result) == 3

    def test_offset(self, tmp_path):
        for i in range(1, 6):
            _write_match(tmp_path, i)
        result = list_matches(str(tmp_path), offset=3)
        assert len(result) == 2
        assert result[0]["match_id"] == 4

    def test_limit_and_offset(self, tmp_path):
        for i in range(1, 6):
            _write_match(tmp_path, i)
        result = list_matches(str(tmp_path), limit=2, offset=2)
        assert [e["match_id"] for e in result] == [3, 4]

    def test_filter_by_winner(self, tmp_path):
        _write_match(tmp_path, 1, winner="🅰️")
        _write_match(tmp_path, 2, winner="🅱️")
        _write_match(tmp_path, 3, winner="🅰️")
        result = list_matches(str(tmp_path), winner="🅰️")
        assert len(result) == 2
        assert all(e["winner"] == "🅰️" for e in result)

    def test_filter_by_bot(self, tmp_path):
        _write_match(tmp_path, 1, players=[
            {"emoji": "🅰️", "name": "A", "bio": "", "author": "t"},
            {"emoji": "🅱️", "name": "B", "bio": "", "author": "t"},
        ])
        _write_match(tmp_path, 2, players=[
            {"emoji": "🅾️", "name": "C", "bio": "", "author": "t"},
            {"emoji": "🅱️", "name": "B", "bio": "", "author": "t"},
        ])
        _write_match(tmp_path, 3, players=[
            {"emoji": "🅰️", "name": "A", "bio": "", "author": "t"},
            {"emoji": "🅾️", "name": "C", "bio": "", "author": "t"},
        ])
        result = list_matches(str(tmp_path), bot="🅰️")
        assert len(result) == 2
        assert {e["match_id"] for e in result} == {1, 3}

    def test_filter_by_date_range(self, tmp_path):
        _write_match(tmp_path, 1, date="2026-01-01T00:00:00+00:00")
        _write_match(tmp_path, 2, date="2026-06-15T00:00:00+00:00")
        _write_match(tmp_path, 3, date="2026-12-31T00:00:00+00:00")
        result = list_matches(str(tmp_path), after="2026-01-31", before="2026-12-01")
        assert len(result) == 1
        assert result[0]["match_id"] == 2


# --- get_latest_match ---


class TestGetLatestMatch:
    def test_returns_highest_id(self, tmp_path):
        _write_match(tmp_path, 1)
        _write_match(tmp_path, 5)
        _write_match(tmp_path, 3)
        match = get_latest_match(str(tmp_path))
        assert match["match_id"] == 5

    def test_returns_none_when_empty(self, tmp_path):
        assert get_latest_match(str(tmp_path)) is None
