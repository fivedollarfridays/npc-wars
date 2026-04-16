"""Tests for data/seasons.py — game-agnostic season manager."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from data.seasons import (
    create_season,
    get_standings,
    init_seasons_tables,
    promote_relegate,
    record_result,
)

TIERS = ("Bronze", "Silver", "Gold", "Diamond")

# --- Kill Switch scoring: kills * 3 + placement_score ---
KS_SCORING = {
    "type": "kill_switch",
    "kill_points": 3,
    "placement_points": {1: 10, 2: 7, 3: 5, 4: 3},
}

# --- Code Circuit scoring: F1 points ---
CC_SCORING = {
    "type": "code_circuit",
    "position_points": {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1},
}


def _make_conn() -> tuple[sqlite3.Connection, Path]:
    tmp = tempfile.mkdtemp()
    db_path = Path(tmp) / "test_seasons.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    init_seasons_tables(conn)
    return conn, db_path


class TestCreateSeason:
    def test_creates_season_returns_id(self):
        conn, _ = _make_conn()
        sid = create_season(conn, "KS Season 1", {"episodes": 10}, KS_SCORING)
        assert isinstance(sid, int)
        assert sid >= 1

    def test_stores_name_and_config(self):
        conn, _ = _make_conn()
        sid = create_season(conn, "CC Championship", {"episodes": 8}, CC_SCORING)
        row = conn.execute("SELECT name FROM seasons WHERE id = ?", (sid,)).fetchone()
        assert row["name"] == "CC Championship"

    def test_multiple_seasons(self):
        conn, _ = _make_conn()
        s1 = create_season(conn, "S1", {"episodes": 5}, KS_SCORING)
        s2 = create_season(conn, "S2", {"episodes": 5}, CC_SCORING)
        assert s1 != s2


class TestRecordResult:
    def test_record_ks_result(self):
        conn, _ = _make_conn()
        sid = create_season(conn, "KS S1", {"episodes": 10}, KS_SCORING)
        record_result(sid, {"participant": "🐉", "kills": 4, "placement": 1}, conn=conn)
        standings = get_standings(sid, conn=conn)
        assert len(standings) == 1
        assert standings[0]["participant"] == "🐉"
        # kills * 3 + placement_points[1] = 12 + 10 = 22
        assert standings[0]["points"] == 22

    def test_record_cc_result(self):
        conn, _ = _make_conn()
        sid = create_season(conn, "CC S1", {"episodes": 8}, CC_SCORING)
        record_result(sid, {"participant": "car_A", "position": 1}, conn=conn)
        standings = get_standings(sid, conn=conn)
        assert standings[0]["points"] == 25

    def test_record_five_results_standings_correct(self):
        conn, _ = _make_conn()
        sid = create_season(conn, "KS S1", {"episodes": 10}, KS_SCORING)
        # 5 matches with different participants
        results = [
            {"participant": "🐉", "kills": 3, "placement": 1},  # 9+10=19
            {"participant": "🦊", "kills": 2, "placement": 2},  # 6+7=13
            {"participant": "🐉", "kills": 1, "placement": 3},  # 3+5=8
            {"participant": "🦊", "kills": 5, "placement": 1},  # 15+10=25
            {"participant": "🐸", "kills": 0, "placement": 4},  # 0+3=3
        ]
        for r in results:
            record_result(sid, r, conn=conn)

        standings = get_standings(sid, conn=conn)
        # 🦊: 13+25=38, 🐉: 19+8=27, 🐸: 3
        assert standings[0]["participant"] == "🦊"
        assert standings[0]["points"] == 38
        assert standings[1]["participant"] == "🐉"
        assert standings[1]["points"] == 27
        assert standings[2]["participant"] == "🐸"
        assert standings[2]["points"] == 3

    def test_unknown_placement_scores_zero(self):
        conn, _ = _make_conn()
        sid = create_season(conn, "KS S1", {"episodes": 10}, KS_SCORING)
        record_result(sid, {"participant": "🐉", "kills": 2, "placement": 8}, conn=conn)
        standings = get_standings(sid, conn=conn)
        # kills * 3 + 0 (placement 8 not in map) = 6
        assert standings[0]["points"] == 6


class TestGetStandings:
    def test_empty_season(self):
        conn, _ = _make_conn()
        sid = create_season(conn, "Empty", {"episodes": 5}, KS_SCORING)
        standings = get_standings(sid, conn=conn)
        assert standings == []

    def test_tier_assignments(self):
        conn, _ = _make_conn()
        sid = create_season(
            conn,
            "Tiered",
            {"episodes": 10, "tier_thresholds": {"Diamond": 0.1, "Gold": 0.3, "Silver": 0.6}},
            KS_SCORING,
        )
        # 10 participants, tiers: top 10% Diamond, top 30% Gold, top 60% Silver, rest Bronze
        for i, emoji in enumerate(["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]):
            record_result(
                sid,
                {"participant": emoji, "kills": 10 - i, "placement": 1},
                conn=conn,
            )
        standings = get_standings(sid, conn=conn)
        assert len(standings) == 10
        # Top 10% = 1 player → Diamond
        assert standings[0]["tier"] == "Diamond"
        # Next up to 30% = positions 2-3 → Gold
        assert standings[1]["tier"] == "Gold"
        assert standings[2]["tier"] == "Gold"
        # Next up to 60% = positions 4-6 → Silver
        assert standings[3]["tier"] == "Silver"
        assert standings[5]["tier"] == "Silver"
        # Rest → Bronze
        assert standings[6]["tier"] == "Bronze"
        assert standings[9]["tier"] == "Bronze"

    def test_default_tiers_when_no_thresholds(self):
        conn, _ = _make_conn()
        sid = create_season(conn, "No Tiers", {"episodes": 5}, KS_SCORING)
        record_result(sid, {"participant": "🐉", "kills": 5, "placement": 1}, conn=conn)
        standings = get_standings(sid, conn=conn)
        # Default thresholds should still assign a tier
        assert standings[0]["tier"] in TIERS


class TestPromoteRelegate:
    def test_promotion_relegation(self):
        conn, _ = _make_conn()
        sid = create_season(
            conn,
            "Promo",
            {
                "episodes": 10,
                "tier_thresholds": {"Diamond": 0.25, "Gold": 0.5, "Silver": 0.75},
                "promote_top_n": 1,
                "relegate_bottom_n": 1,
            },
            KS_SCORING,
        )
        # 4 participants → Diamond(1), Gold(1), Silver(1), Bronze(1)
        for emoji, kills in [("A", 10), ("B", 7), ("C", 4), ("D", 1)]:
            record_result(sid, {"participant": emoji, "kills": kills, "placement": 1}, conn=conn)

        changes = promote_relegate(sid, conn=conn)
        # Top of each tier promoted (except Diamond), bottom of each tier relegated (except Bronze)
        promoted = [c for c in changes if c["action"] == "promote"]
        relegated = [c for c in changes if c["action"] == "relegate"]
        assert len(promoted) >= 1
        assert len(relegated) >= 1

    def test_no_changes_single_participant(self):
        conn, _ = _make_conn()
        sid = create_season(
            conn,
            "Solo",
            {"episodes": 5, "promote_top_n": 1, "relegate_bottom_n": 1},
            KS_SCORING,
        )
        record_result(sid, {"participant": "🐉", "kills": 5, "placement": 1}, conn=conn)
        changes = promote_relegate(sid, conn=conn)
        assert changes == []


class TestCodeCircuitScoring:
    def test_f1_points_system(self):
        conn, _ = _make_conn()
        sid = create_season(conn, "CC GP", {"episodes": 10}, CC_SCORING)
        record_result(sid, {"participant": "car_A", "position": 1}, conn=conn)  # 25
        record_result(sid, {"participant": "car_B", "position": 2}, conn=conn)  # 18
        record_result(sid, {"participant": "car_A", "position": 3}, conn=conn)  # 15
        standings = get_standings(sid, conn=conn)
        assert standings[0]["participant"] == "car_A"
        assert standings[0]["points"] == 40  # 25 + 15
        assert standings[1]["participant"] == "car_B"
        assert standings[1]["points"] == 18

    def test_unscored_position_gives_zero(self):
        conn, _ = _make_conn()
        sid = create_season(conn, "CC GP", {"episodes": 10}, CC_SCORING)
        record_result(sid, {"participant": "car_Z", "position": 20}, conn=conn)
        standings = get_standings(sid, conn=conn)
        assert standings[0]["points"] == 0
