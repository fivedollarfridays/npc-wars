"""Tests for data/leaderboard.py — stats aggregation, rankings."""

import json

import pytest

from data.leaderboard import aggregate_stats, get_bot_stats, get_rankings, load_match


# --- Fixtures ---


def _make_match(winner="🅰️", players=None, stats=None, eliminations=None, match_id=1):
    """Build a minimal match dict for testing."""
    if players is None:
        players = [
            {"emoji": "🅰️", "name": "A", "bio": "", "author": "test"},
            {"emoji": "🅱️", "name": "B", "bio": "", "author": "test"},
        ]
    if stats is None:
        stats = {
            "🅰️": {"kills": 1, "damage_dealt": 50, "damage_taken": 20, "rounds_survived": 10},
            "🅱️": {"kills": 0, "damage_dealt": 20, "damage_taken": 50, "rounds_survived": 8},
        }
    if eliminations is None:
        eliminations = [
            {"emoji": "🅱️", "round": 8, "killed_by": "🅰️", "cause": "combat"},
        ]
    return {
        "match_id": match_id,
        "date": "2026-01-01T00:00:00+00:00",
        "grid_size": 10,
        "players": players,
        "rounds": [],
        "eliminations": eliminations,
        "winner": winner,
        "stats": stats,
        "duration_rounds": 10,
    }


# --- aggregate_stats ---


class TestAggregateStats:
    def test_single_match_winner_gets_win(self):
        match = _make_match(winner="🅰️")
        result = aggregate_stats([match])
        assert result["🅰️"]["wins"] == 1
        assert result["🅱️"]["wins"] == 0

    def test_single_match_loser_gets_loss(self):
        match = _make_match(winner="🅰️")
        result = aggregate_stats([match])
        assert result["🅱️"]["losses"] == 1
        assert result["🅰️"]["losses"] == 0

    def test_kills_aggregated(self):
        match = _make_match(stats={
            "🅰️": {"kills": 2, "damage_dealt": 100, "damage_taken": 0, "rounds_survived": 10},
            "🅱️": {"kills": 0, "damage_dealt": 0, "damage_taken": 100, "rounds_survived": 5},
        })
        result = aggregate_stats([match])
        assert result["🅰️"]["kills"] == 2
        assert result["🅱️"]["kills"] == 0

    def test_damage_aggregated(self):
        match = _make_match(stats={
            "🅰️": {"kills": 1, "damage_dealt": 80, "damage_taken": 30, "rounds_survived": 10},
            "🅱️": {"kills": 0, "damage_dealt": 30, "damage_taken": 80, "rounds_survived": 5},
        })
        result = aggregate_stats([match])
        assert result["🅰️"]["damage_dealt"] == 80
        assert result["🅰️"]["damage_taken"] == 30

    def test_matches_played_counted(self):
        m1 = _make_match(winner="🅰️", match_id=1)
        m2 = _make_match(winner="🅱️", match_id=2)
        result = aggregate_stats([m1, m2])
        assert result["🅰️"]["matches_played"] == 2
        assert result["🅱️"]["matches_played"] == 2

    def test_multi_match_cumulative_kills(self):
        m1 = _make_match(match_id=1, stats={
            "🅰️": {"kills": 1, "damage_dealt": 50, "damage_taken": 0, "rounds_survived": 10},
            "🅱️": {"kills": 0, "damage_dealt": 0, "damage_taken": 50, "rounds_survived": 5},
        })
        m2 = _make_match(match_id=2, stats={
            "🅰️": {"kills": 2, "damage_dealt": 80, "damage_taken": 10, "rounds_survived": 15},
            "🅱️": {"kills": 0, "damage_dealt": 10, "damage_taken": 80, "rounds_survived": 8},
        })
        result = aggregate_stats([m1, m2])
        assert result["🅰️"]["kills"] == 3

    def test_avg_placement_winner_is_first(self):
        """In a 2-player match, winner placement = 1."""
        match = _make_match(winner="🅰️")
        result = aggregate_stats([match])
        assert result["🅰️"]["avg_placement"] == 1.0

    def test_avg_placement_loser_in_two_player(self):
        """In a 2-player match, loser placement = 2."""
        match = _make_match(winner="🅰️")
        result = aggregate_stats([match])
        assert result["🅱️"]["avg_placement"] == 2.0

    def test_avg_placement_three_players(self):
        """3-player match: winner=1, second_out=2, first_out=3."""
        match = _make_match(
            winner="🅰️",
            players=[
                {"emoji": "🅰️", "name": "A", "bio": "", "author": "t"},
                {"emoji": "🅱️", "name": "B", "bio": "", "author": "t"},
                {"emoji": "🅾️", "name": "C", "bio": "", "author": "t"},
            ],
            stats={
                "🅰️": {"kills": 2, "damage_dealt": 100, "damage_taken": 0, "rounds_survived": 20},
                "🅱️": {"kills": 0, "damage_dealt": 30, "damage_taken": 50, "rounds_survived": 10},
                "🅾️": {"kills": 0, "damage_dealt": 10, "damage_taken": 60, "rounds_survived": 5},
            },
            eliminations=[
                {"emoji": "🅾️", "round": 5, "killed_by": "🅰️", "cause": "combat"},
                {"emoji": "🅱️", "round": 10, "killed_by": "🅰️", "cause": "combat"},
            ],
        )
        result = aggregate_stats([match])
        assert result["🅰️"]["avg_placement"] == 1.0
        assert result["🅱️"]["avg_placement"] == 2.0
        assert result["🅾️"]["avg_placement"] == 3.0

    def test_avg_placement_averaged_over_matches(self):
        """Bot that wins one, loses last in another → avg 1.5."""
        m1 = _make_match(winner="🅰️", match_id=1)
        m2 = _make_match(winner="🅱️", match_id=2,
                         eliminations=[{"emoji": "🅰️", "round": 8, "killed_by": "🅱️", "cause": "combat"}])
        result = aggregate_stats([m1, m2])
        assert result["🅰️"]["avg_placement"] == 1.5

    def test_win_rate_single_win(self):
        match = _make_match(winner="🅰️")
        result = aggregate_stats([match])
        assert result["🅰️"]["win_rate"] == 1.0
        assert result["🅱️"]["win_rate"] == 0.0

    def test_empty_match_list(self):
        assert aggregate_stats([]) == {}


# --- get_rankings ---


class TestGetRankings:
    def _two_bot_stats(self):
        m1 = _make_match(winner="🅰️", match_id=1)
        m2 = _make_match(winner="🅰️", match_id=2)
        return aggregate_stats([m1, m2])

    def test_sort_by_wins(self):
        stats = self._two_bot_stats()
        ranked = get_rankings(stats, sort_by="wins")
        assert ranked[0]["emoji"] == "🅰️"

    def test_sort_by_kills(self):
        m = _make_match(stats={
            "🅰️": {"kills": 0, "damage_dealt": 0, "damage_taken": 50, "rounds_survived": 5},
            "🅱️": {"kills": 3, "damage_dealt": 150, "damage_taken": 0, "rounds_survived": 20},
        })
        stats = aggregate_stats([m])
        ranked = get_rankings(stats, sort_by="kills")
        assert ranked[0]["emoji"] == "🅱️"

    def test_sort_by_win_rate(self):
        stats = self._two_bot_stats()
        ranked = get_rankings(stats, sort_by="win_rate")
        assert ranked[0]["emoji"] == "🅰️"

    def test_sort_by_avg_placement(self):
        """Lower avg_placement is better (1st > 2nd)."""
        stats = self._two_bot_stats()
        ranked = get_rankings(stats, sort_by="avg_placement")
        assert ranked[0]["emoji"] == "🅰️"

    def test_rankings_include_emoji_field(self):
        stats = aggregate_stats([_make_match()])
        ranked = get_rankings(stats)
        assert "emoji" in ranked[0]

    def test_invalid_sort_raises(self):
        stats = aggregate_stats([_make_match()])
        with pytest.raises(ValueError):
            get_rankings(stats, sort_by="invalid_field")


# --- get_bot_stats ---


class TestGetBotStats:
    def test_returns_stats_for_known_bot(self):
        stats = aggregate_stats([_make_match(winner="🅰️")])
        bot = get_bot_stats(stats, "🅰️")
        assert bot["wins"] == 1

    def test_returns_none_for_unknown_bot(self):
        stats = aggregate_stats([_make_match()])
        assert get_bot_stats(stats, "❓") is None


# --- load_match ---


class TestLoadMatch:
    def test_loads_valid_json(self, tmp_path):
        match = _make_match()
        path = tmp_path / "match_001.json"
        path.write_text(json.dumps(match))
        loaded = load_match(str(path))
        assert loaded["match_id"] == 1

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_match(str(tmp_path / "nonexistent.json"))
