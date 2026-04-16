"""Tests for season Discord commands and automation."""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock

from data.seasons import create_season, init_seasons_tables, record_result
from discord_bot.commands.season_commands import register_commands
from discord_bot.commands.season_helpers import (
    check_season_finale,
    format_season_created,
    format_season_standings,
    format_weekly_summary,
    record_match_to_season,
)

# ---------------------------------------------------------------------------
# Scoring presets
# ---------------------------------------------------------------------------

KS_SCORING = {
    "type": "kill_switch",
    "kill_points": 3,
    "placement_points": {1: 10, 2: 7, 3: 5, 4: 3},
}

CC_SCORING = {
    "type": "code_circuit",
    "position_points": {1: 25, 2: 18, 3: 15},
}


def _make_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_seasons_tables(conn)
    return conn


# ---------------------------------------------------------------------------
# format_season_created
# ---------------------------------------------------------------------------


class TestFormatSeasonCreated:
    def test_returns_embed_dict(self):
        result = format_season_created("Season Alpha", 1, "kill_switch")
        assert result["title"]
        assert "Season Alpha" in result["description"]

    def test_includes_game_label(self):
        result = format_season_created("GP 2026", 5, "code_circuit")
        assert "Code Circuit" in result["description"] or "code_circuit" in result["description"]


# ---------------------------------------------------------------------------
# format_season_standings
# ---------------------------------------------------------------------------


class TestFormatSeasonStandings:
    def test_empty_standings(self):
        result = format_season_standings("Empty Season", [])
        assert "No results" in result["description"]

    def test_standings_with_tiers(self):
        standings = [
            {"participant": "A", "points": 50, "tier": "Diamond"},
            {"participant": "B", "points": 30, "tier": "Gold"},
            {"participant": "C", "points": 10, "tier": "Bronze"},
        ]
        result = format_season_standings("KS S1", standings)
        assert len(result["fields"]) >= 1
        field_text = result["fields"][0]["value"]
        assert "A" in field_text
        assert "Diamond" in field_text
        assert "50" in field_text

    def test_standings_ordered(self):
        standings = [
            {"participant": "X", "points": 100, "tier": "Diamond"},
            {"participant": "Y", "points": 50, "tier": "Gold"},
        ]
        result = format_season_standings("Test", standings)
        field_text = result["fields"][0]["value"]
        # X should appear before Y
        assert field_text.index("X") < field_text.index("Y")


# ---------------------------------------------------------------------------
# record_match_to_season
# ---------------------------------------------------------------------------


class TestRecordMatchToSeason:
    def test_records_ks_results(self):
        conn = _make_conn()
        sid = create_season(conn, "KS S1", {"total_rounds": 10}, KS_SCORING)
        match_data = {
            "game": "kill_switch",
            "stats": {
                "A": {"kills": 3},
                "B": {"kills": 1},
            },
            "eliminations": [
                {"emoji": "B", "round": 5},
            ],
            "winner": "A",
            "participants": ["A", "B"],
        }
        record_match_to_season(sid, match_data, conn=conn)
        from data.seasons import get_standings

        standings = get_standings(sid, conn=conn)
        assert len(standings) == 2

    def test_records_cc_results(self):
        conn = _make_conn()
        sid = create_season(conn, "CC GP", {"total_rounds": 8}, CC_SCORING)
        match_data = {
            "game": "code_circuit",
            "results": [
                {"car": "FastCar", "position": 1},
                {"car": "SlowCar", "position": 2},
            ],
        }
        record_match_to_season(sid, match_data, conn=conn)
        from data.seasons import get_standings

        standings = get_standings(sid, conn=conn)
        assert len(standings) == 2
        assert standings[0]["participant"] == "FastCar"
        assert standings[0]["points"] == 25

    def test_ks_placement_from_eliminations(self):
        conn = _make_conn()
        sid = create_season(conn, "KS S1", {"total_rounds": 10}, KS_SCORING)
        match_data = {
            "game": "kill_switch",
            "stats": {"A": {"kills": 2}, "B": {"kills": 0}, "C": {"kills": 1}},
            "eliminations": [
                {"emoji": "B", "round": 3},
                {"emoji": "C", "round": 7},
            ],
            "winner": "A",
            "participants": ["A", "B", "C"],
        }
        record_match_to_season(sid, match_data, conn=conn)
        from data.seasons import get_standings

        standings = get_standings(sid, conn=conn)
        # A wins (placement 1): 2*3 + 10 = 16
        a = next(s for s in standings if s["participant"] == "A")
        assert a["points"] == 16


# ---------------------------------------------------------------------------
# check_season_finale
# ---------------------------------------------------------------------------


class TestCheckSeasonFinale:
    def test_not_finale_when_rounds_remaining(self):
        conn = _make_conn()
        sid = create_season(conn, "S1", {"total_rounds": 10}, KS_SCORING)
        record_result(sid, {"participant": "A", "kills": 1, "placement": 1}, conn=conn)
        assert check_season_finale(sid, conn=conn) is False

    def test_finale_when_all_rounds_complete(self):
        conn = _make_conn()
        sid = create_season(conn, "S1", {"total_rounds": 3}, KS_SCORING)
        for i in range(3):
            record_result(sid, {"participant": "A", "kills": 1, "placement": 1}, conn=conn)
        assert check_season_finale(sid, conn=conn) is True

    def test_finale_when_exceeded(self):
        conn = _make_conn()
        sid = create_season(conn, "S1", {"total_rounds": 2}, KS_SCORING)
        for i in range(5):
            record_result(sid, {"participant": "A", "kills": 1, "placement": 1}, conn=conn)
        assert check_season_finale(sid, conn=conn) is True

    def test_no_total_rounds_never_finale(self):
        conn = _make_conn()
        sid = create_season(conn, "S1", {}, KS_SCORING)
        for i in range(20):
            record_result(sid, {"participant": "A", "kills": 1, "placement": 1}, conn=conn)
        assert check_season_finale(sid, conn=conn) is False


# ---------------------------------------------------------------------------
# format_weekly_summary
# ---------------------------------------------------------------------------


class TestFormatWeeklySummary:
    def test_weekly_summary_structure(self):
        standings = [
            {"participant": "A", "points": 50, "tier": "Diamond"},
            {"participant": "B", "points": 30, "tier": "Gold"},
        ]
        result = format_weekly_summary("KS Season 1", standings)
        assert "Power Rankings" in result["title"]
        assert len(result["fields"]) >= 1

    def test_weekly_summary_empty(self):
        result = format_weekly_summary("Empty", [])
        assert "No results" in result["description"]


# ---------------------------------------------------------------------------
# register_commands
# ---------------------------------------------------------------------------


class TestRegisterCommands:
    def test_registers_season_group(self):
        tree = MagicMock()
        guild = MagicMock()
        conn = _make_conn()
        register_commands(tree, guild, conn)
        tree.add_command.assert_called_once()
        group = tree.add_command.call_args[0][0]
        assert group.name == "season"
