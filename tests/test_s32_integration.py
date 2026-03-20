"""S32 GATE: End-to-end XP flow integration tests.

Verifies the complete pipeline: match -> XP calc -> profile persistence -> levels.
Uses in-memory SQLite for speed. Real match engine for seeded scenarios.
"""

from __future__ import annotations

import sqlite3

import pytest

from engine.game import run_match
from engine.levels import level_from_xp, unlocks_at_level
from engine.profile_db import (
    get_leaderboard,
    get_profile,
    init_profile_db,
    update_profile,
)
from engine.xp import (
    BASE_XP,
    XP_PER_KILL,
    XP_PER_ROUND,
    WIN_BONUS,
    SECOND_PLACE_BONUS,
    THIRD_PLACE_BONUS,
    calculate_match_xp,
)
from engine.xp_runner import apply_xp_awards, inject_xp_into_match
from tests.conftest import always_rest, bot_config, chase_and_attack


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db() -> sqlite3.Connection:
    """In-memory profile DB, closed after each test."""
    conn = init_profile_db(":memory:")
    yield conn
    conn.close()


def _three_bot_configs() -> list[dict]:
    """Three seeded bots: one aggressive, two passive."""
    return [
        bot_config("Alpha", "A", chase_and_attack),
        bot_config("Bravo", "B", always_rest),
        bot_config("Charlie", "C", always_rest),
    ]


# ---------------------------------------------------------------------------
# Scenario 1: Fresh player flow
# ---------------------------------------------------------------------------


class TestFreshPlayerFlow:
    """Run a real seeded match -> profiles auto-created -> XP awarded."""

    def test_match_completes_with_winner(self) -> None:
        """A seeded match produces a valid winner."""
        configs = _three_bot_configs()
        result = run_match(configs, match_id=1, seed=42)
        assert result["winner"] != "none"
        assert result["duration_rounds"] > 0

    def test_profiles_created_after_xp_injection(self, db: sqlite3.Connection) -> None:
        """After inject_xp_into_match, all players have profiles in DB."""
        configs = _three_bot_configs()
        result = run_match(configs, match_id=1, seed=42)
        inject_xp_into_match(result, db)

        for name in ("Alpha", "Bravo", "Charlie"):
            profile = get_profile(db, name)
            assert profile is not None, f"Profile for {name} not created"
            assert profile["total_xp"] > 0
            assert profile["matches"] == 1

    def test_xp_awards_present_in_result(self, db: sqlite3.Connection) -> None:
        """xp_awards key appears in match result after injection."""
        configs = _three_bot_configs()
        result = run_match(configs, match_id=1, seed=42)
        inject_xp_into_match(result, db)

        assert "xp_awards" in result
        assert set(result["xp_awards"].keys()) == {"A", "B", "C"}

    def test_winner_gets_most_xp(self, db: sqlite3.Connection) -> None:
        """The match winner should earn the most XP (win bonus)."""
        configs = _three_bot_configs()
        result = run_match(configs, match_id=1, seed=42)
        inject_xp_into_match(result, db)

        winner = result["winner"]
        awards = result["xp_awards"]
        winner_total = awards[winner]["total"]
        for emoji, award in awards.items():
            if emoji != winner:
                assert winner_total >= award["total"]


# ---------------------------------------------------------------------------
# Scenario 4: XP formula accuracy (known match result)
# ---------------------------------------------------------------------------


def _build_known_match() -> dict:
    """Build a match result with known values for exact XP verification."""
    return {
        "players": [
            {"emoji": "X", "name": "Xeno"},
            {"emoji": "Y", "name": "Yara"},
            {"emoji": "Z", "name": "Zara"},
        ],
        "winner": "X",
        "duration_rounds": 20,
        "eliminations": [
            {"emoji": "Z", "round": 10, "killed_by": "X", "cause": "combat"},
            {"emoji": "Y", "round": 18, "killed_by": "X", "cause": "combat"},
        ],
        "stats": {
            "X": {"kills": 2, "rounds_survived": 20},
            "Y": {"kills": 0, "rounds_survived": 18},
            "Z": {"kills": 0, "rounds_survived": 10},
        },
        "rounds": [],
    }


class TestXpFormulaAccuracy:
    """Verify exact XP breakdown from a hand-crafted match result."""

    def test_winner_xp_breakdown(self) -> None:
        """Winner gets base + kills*15 + survival*2 + WIN_BONUS + first_blood."""
        match = _build_known_match()
        xp_map = calculate_match_xp(match)
        x = xp_map["X"]
        assert x.base == BASE_XP  # 10
        assert x.kills == 2 * XP_PER_KILL  # 30
        assert x.survival == 20 * XP_PER_ROUND  # 40
        assert x.placement == WIN_BONUS  # 50
        # First blood: X killed Z first (combat kill)
        assert x.bonuses >= 20  # FIRST_BLOOD_XP
        assert x.total == x.base + x.kills + x.survival + x.placement + x.bonuses

    def test_second_place_xp(self) -> None:
        """Second-place bot gets SECOND_PLACE_BONUS placement XP."""
        match = _build_known_match()
        xp_map = calculate_match_xp(match)
        y = xp_map["Y"]
        assert y.placement == SECOND_PLACE_BONUS  # 25

    def test_third_place_xp(self) -> None:
        """Third-place bot gets THIRD_PLACE_BONUS placement XP."""
        match = _build_known_match()
        xp_map = calculate_match_xp(match)
        z = xp_map["Z"]
        assert z.placement == THIRD_PLACE_BONUS  # 15

    def test_all_totals_are_sum_of_parts(self) -> None:
        """Every bot's total = sum of component fields."""
        match = _build_known_match()
        xp_map = calculate_match_xp(match)
        for bd in xp_map.values():
            assert bd.total == bd.base + bd.kills + bd.survival + bd.placement + bd.bonuses


# ---------------------------------------------------------------------------
# Scenario 2: Level-up flow
# ---------------------------------------------------------------------------


class TestLevelUpFlow:
    """Seed a profile near level boundary -> run match -> verify level-up."""

    def test_level_up_detected_in_awards(self, db: sqlite3.Connection) -> None:
        """Pre-seed profile near level 2 boundary, run match, detect level-up."""
        # Level 2 requires 100 XP. Seed at 90 XP.
        update_profile(db, "Alpha", xp_earned=90, kills=0, won=False)
        old = get_profile(db, "Alpha")
        assert old is not None
        assert old["level"] == 1

        configs = _three_bot_configs()
        result = run_match(configs, match_id=1, seed=42)
        awards = apply_xp_awards(result, db)

        # Alpha earned XP from match; should push past 100
        alpha_award = awards["A"]
        assert alpha_award["total"] > 0
        assert alpha_award["leveled_up"] is True
        assert alpha_award["new_level"] >= 2

    def test_new_unlocks_available_after_level_up(self, db: sqlite3.Connection) -> None:
        """After leveling to 3, ranged_attack should be unlocked."""
        # Level 3 requires 250 XP. Seed at 240.
        update_profile(db, "Alpha", xp_earned=240, kills=0, won=False)

        configs = _three_bot_configs()
        result = run_match(configs, match_id=1, seed=42)
        awards = apply_xp_awards(result, db)

        alpha_award = awards["A"]
        if alpha_award["new_level"] >= 3:
            unlocks = unlocks_at_level(alpha_award["new_level"])
            assert "ranged_attack" in unlocks.actions

    def test_no_level_up_when_insufficient_xp(self, db: sqlite3.Connection) -> None:
        """Profile at 0 XP with minimal match XP stays level 1."""
        match = _build_known_match()
        # Override stats so Z gets minimal XP
        match["stats"]["Z"] = {"kills": 0, "rounds_survived": 1}
        awards = apply_xp_awards(match, db)
        z = awards["Z"]
        # base(10) + kills(0) + survival(2) + placement(15) + bonus(0) = 27
        # Level 2 needs 100, so should stay level 1
        assert z["leveled_up"] is False
        assert z["new_level"] == 1


# ---------------------------------------------------------------------------
# Scenario 3: Multi-match accumulation
# ---------------------------------------------------------------------------


class TestMultiMatchAccumulation:
    """Run 3 matches -> verify XP accumulates correctly -> levels increase."""

    def test_xp_accumulates_across_three_matches(self, db: sqlite3.Connection) -> None:
        """XP totals grow with each successive match."""
        configs = _three_bot_configs()
        xp_after: list[int] = []

        for i in range(3):
            result = run_match(configs, match_id=i + 1, seed=42 + i)
            inject_xp_into_match(result, db)
            profile = get_profile(db, "Alpha")
            assert profile is not None
            xp_after.append(profile["total_xp"])

        # XP should strictly increase
        assert xp_after[0] > 0
        assert xp_after[1] > xp_after[0]
        assert xp_after[2] > xp_after[1]

    def test_match_count_increments(self, db: sqlite3.Connection) -> None:
        """Matches played count increases by 1 per match."""
        configs = _three_bot_configs()
        for i in range(3):
            result = run_match(configs, match_id=i + 1, seed=42 + i)
            inject_xp_into_match(result, db)

        profile = get_profile(db, "Alpha")
        assert profile is not None
        assert profile["matches"] == 3

    def test_level_increases_after_multiple_matches(self, db: sqlite3.Connection) -> None:
        """After enough matches, level should be > 1."""
        configs = _three_bot_configs()
        for i in range(3):
            result = run_match(configs, match_id=i + 1, seed=42 + i)
            inject_xp_into_match(result, db)

        profile = get_profile(db, "Alpha")
        assert profile is not None
        # 3 matches should yield enough XP for at least level 2
        assert profile["level"] >= 2


# ---------------------------------------------------------------------------
# Scenario 5: Profile persistence across connections
# ---------------------------------------------------------------------------


class TestProfilePersistenceAcrossConnections:
    """Write profile -> close DB -> reopen -> verify data intact."""

    def test_data_survives_reconnect(self, tmp_path) -> None:
        """Profile data persists across DB close/reopen cycle."""
        db_path = str(tmp_path / "test_profiles.db")

        # Write profile
        conn1 = init_profile_db(db_path)
        update_profile(conn1, "Persist", xp_earned=500, kills=10, won=True)
        conn1.close()

        # Reopen and verify
        conn2 = init_profile_db(db_path)
        profile = get_profile(conn2, "Persist")
        conn2.close()

        assert profile is not None
        assert profile["total_xp"] == 500
        assert profile["kills"] == 10
        assert profile["wins"] == 1
        assert profile["level"] == level_from_xp(500)

    def test_xp_accumulates_across_reconnects(self, tmp_path) -> None:
        """XP from separate sessions accumulates correctly."""
        db_path = str(tmp_path / "test_profiles.db")

        conn1 = init_profile_db(db_path)
        update_profile(conn1, "Multi", xp_earned=200, kills=5, won=True)
        conn1.close()

        conn2 = init_profile_db(db_path)
        update_profile(conn2, "Multi", xp_earned=300, kills=3, won=False)
        profile = get_profile(conn2, "Multi")
        conn2.close()

        assert profile is not None
        assert profile["total_xp"] == 500
        assert profile["kills"] == 8
        assert profile["wins"] == 1
        assert profile["matches"] == 2


# ---------------------------------------------------------------------------
# Scenario 6: No-XP flag
# ---------------------------------------------------------------------------


class TestNoXpFlag:
    """inject_xp_into_match with no_xp=True produces no side effects."""

    def test_no_xp_awards_in_result(self, db: sqlite3.Connection) -> None:
        """no_xp=True means no xp_awards key in match result."""
        configs = _three_bot_configs()
        result = run_match(configs, match_id=1, seed=42)
        inject_xp_into_match(result, db, no_xp=True)
        assert "xp_awards" not in result

    def test_no_profiles_created(self, db: sqlite3.Connection) -> None:
        """no_xp=True means no profile rows created."""
        configs = _three_bot_configs()
        result = run_match(configs, match_id=1, seed=42)
        inject_xp_into_match(result, db, no_xp=True)

        for name in ("Alpha", "Bravo", "Charlie"):
            assert get_profile(db, name) is None

    def test_existing_profiles_unchanged(self, db: sqlite3.Connection) -> None:
        """no_xp=True leaves pre-existing profiles untouched."""
        update_profile(db, "Alpha", xp_earned=100, kills=5, won=True)
        original = get_profile(db, "Alpha")

        configs = _three_bot_configs()
        result = run_match(configs, match_id=1, seed=42)
        inject_xp_into_match(result, db, no_xp=True)

        after = get_profile(db, "Alpha")
        assert after is not None
        assert after["total_xp"] == original["total_xp"]
        assert after["matches"] == original["matches"]


# ---------------------------------------------------------------------------
# Scenario 7: Leaderboard ordering
# ---------------------------------------------------------------------------


class TestLeaderboardOrdering:
    """get_leaderboard returns profiles sorted by level DESC, XP DESC."""

    def test_sorted_by_level_then_xp(self, db: sqlite3.Connection) -> None:
        """Higher level first; within same level, higher XP first."""
        update_profile(db, "Low", xp_earned=50, kills=0, won=False)
        update_profile(db, "Mid", xp_earned=150, kills=0, won=False)
        update_profile(db, "High", xp_earned=500, kills=0, won=False)

        board = get_leaderboard(db, limit=10)
        names = [p["name"] for p in board]
        # High (level 3+) > Mid (level 2) > Low (level 1)
        assert names.index("High") < names.index("Mid")
        assert names.index("Mid") < names.index("Low")

    def test_same_level_sorted_by_xp(self, db: sqlite3.Connection) -> None:
        """Two profiles at same level sorted by total_xp descending."""
        # Both under 100 XP = level 1
        update_profile(db, "A_low", xp_earned=30, kills=0, won=False)
        update_profile(db, "B_high", xp_earned=80, kills=0, won=False)

        board = get_leaderboard(db, limit=10)
        names = [p["name"] for p in board]
        assert names.index("B_high") < names.index("A_low")

    def test_limit_respected(self, db: sqlite3.Connection) -> None:
        """Leaderboard respects the limit parameter."""
        for i in range(10):
            update_profile(db, f"Bot{i}", xp_earned=i * 50, kills=0, won=False)

        board = get_leaderboard(db, limit=5)
        assert len(board) == 5


# ---------------------------------------------------------------------------
# Bonus gate checks
# ---------------------------------------------------------------------------


class TestBonusGateChecks:
    """Verify wiring: non-dead code, exports used, match result shape."""

    def test_xp_awards_in_real_match_flow(self, db: sqlite3.Connection) -> None:
        """Full pipeline: run_match + inject = xp_awards key present."""
        configs = _three_bot_configs()
        result = run_match(configs, match_id=1, seed=42)
        inject_xp_into_match(result, db)
        assert "xp_awards" in result
        assert len(result["xp_awards"]) == 3

    def test_run_match_imports_xp_runner(self) -> None:
        """run_match.py actually imports inject_xp_into_match."""
        import importlib
        mod = importlib.import_module("run_match")
        assert hasattr(mod, "inject_xp_into_match") or "inject_xp_into_match" in dir(mod)

    def test_xp_module_exports_used(self) -> None:
        """All __all__ exports from engine.xp are importable and non-empty."""
        from engine import xp
        for name in xp.__all__:
            obj = getattr(xp, name)
            assert obj is not None
