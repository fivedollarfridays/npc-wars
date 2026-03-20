"""Tests for XP integration into match runner — engine/xp_runner.py."""

from __future__ import annotations

import sqlite3

import pytest

from engine.xp_runner import apply_xp_awards


# --- Helpers ---

def _minimal_match(
    players: list[dict] | None = None,
    eliminations: list[dict] | None = None,
    winner: str = "A",
    duration_rounds: int = 10,
    stats: dict | None = None,
    rounds: list[dict] | None = None,
) -> dict:
    """Build a minimal match result dict for testing."""
    if players is None:
        players = [
            {"emoji": "A", "name": "BotA"},
            {"emoji": "B", "name": "BotB"},
            {"emoji": "C", "name": "BotC"},
        ]
    if eliminations is None:
        eliminations = [
            {"emoji": "C", "round": 5, "killed_by": "A", "cause": "combat"},
            {"emoji": "B", "round": 8, "killed_by": "A", "cause": "combat"},
        ]
    if stats is None:
        stats = {
            "A": {"kills": 2, "rounds_survived": 10},
            "B": {"kills": 0, "rounds_survived": 8},
            "C": {"kills": 0, "rounds_survived": 5},
        }
    return {
        "players": players,
        "eliminations": eliminations,
        "winner": winner,
        "duration_rounds": duration_rounds,
        "stats": stats,
        "rounds": rounds or [],
    }


@pytest.fixture
def db_conn():
    """In-memory profile DB for testing."""
    from engine.profile_db import init_profile_db

    conn = init_profile_db(":memory:")
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Cycle 1: apply_xp_awards returns correct structure
# ---------------------------------------------------------------------------


class TestApplyXpAwardsStructure:
    def test_returns_dict_keyed_by_emoji(self, db_conn: sqlite3.Connection) -> None:
        """apply_xp_awards returns a dict with one entry per player."""
        match = _minimal_match()
        result = apply_xp_awards(match, db_conn)
        assert set(result.keys()) == {"A", "B", "C"}

    def test_each_entry_has_required_fields(self, db_conn: sqlite3.Connection) -> None:
        """Each entry must have base, kills, survival, placement, bonuses, total, new_level, leveled_up."""
        match = _minimal_match()
        result = apply_xp_awards(match, db_conn)
        required = {"base", "kills", "survival", "placement", "bonuses", "total", "new_level", "leveled_up"}
        for emoji, award in result.items():
            assert required.issubset(set(award.keys())), f"Missing keys for {emoji}: {required - set(award.keys())}"

    def test_total_is_sum_of_components(self, db_conn: sqlite3.Connection) -> None:
        """Total equals base + kills + survival + placement + bonuses."""
        match = _minimal_match()
        result = apply_xp_awards(match, db_conn)
        for award in result.values():
            assert award["total"] == award["base"] + award["kills"] + award["survival"] + award["placement"] + award["bonuses"]


# ---------------------------------------------------------------------------
# Cycle 2: Profile persistence and level-up detection
# ---------------------------------------------------------------------------


class TestProfilePersistence:
    def test_profiles_created_in_db(self, db_conn: sqlite3.Connection) -> None:
        """apply_xp_awards creates/updates profiles in the DB."""
        from engine.profile_db import get_profile

        match = _minimal_match()
        apply_xp_awards(match, db_conn)
        for player in match["players"]:
            profile = get_profile(db_conn, player["name"])
            assert profile is not None, f"Profile for {player['name']} not found"
            assert profile["total_xp"] > 0

    def test_winner_gets_win_credited(self, db_conn: sqlite3.Connection) -> None:
        """Winner's profile has wins incremented."""
        from engine.profile_db import get_profile

        match = _minimal_match()
        apply_xp_awards(match, db_conn)
        winner_profile = get_profile(db_conn, "BotA")
        loser_profile = get_profile(db_conn, "BotB")
        assert winner_profile["wins"] == 1
        assert loser_profile["wins"] == 0

    def test_kills_persisted(self, db_conn: sqlite3.Connection) -> None:
        """Kill counts are persisted to profiles."""
        from engine.profile_db import get_profile

        match = _minimal_match()
        apply_xp_awards(match, db_conn)
        profile = get_profile(db_conn, "BotA")
        assert profile["kills"] == 2

    def test_xp_accumulates_across_matches(self, db_conn: sqlite3.Connection) -> None:
        """Running apply_xp_awards twice accumulates XP."""
        from engine.profile_db import get_profile

        match = _minimal_match()
        apply_xp_awards(match, db_conn)
        xp_after_1 = get_profile(db_conn, "BotA")["total_xp"]
        apply_xp_awards(match, db_conn)
        xp_after_2 = get_profile(db_conn, "BotA")["total_xp"]
        assert xp_after_2 > xp_after_1


class TestLevelUpDetection:
    def test_leveled_up_false_for_new_bot(self, db_conn: sqlite3.Connection) -> None:
        """First match with low XP: leveled_up should be False (stays level 1)."""
        match = _minimal_match(
            stats={
                "A": {"kills": 0, "rounds_survived": 1},
                "B": {"kills": 0, "rounds_survived": 1},
                "C": {"kills": 0, "rounds_survived": 1},
            },
            eliminations=[],
            winner="none",
        )
        result = apply_xp_awards(match, db_conn)
        # With only base XP (10), should stay level 1
        for award in result.values():
            assert award["leveled_up"] is False
            assert award["new_level"] == 1

    def test_leveled_up_true_after_enough_xp(self, db_conn: sqlite3.Connection) -> None:
        """After accumulating enough XP, leveled_up should be True."""
        from engine.profile_db import update_profile

        # Pre-seed BotA with 90 XP (level 1, needs 100 for level 2)
        update_profile(db_conn, "BotA", xp_earned=90, kills=0, won=False)

        match = _minimal_match()  # Winner BotA gets lots of XP
        result = apply_xp_awards(match, db_conn)
        # BotA should have leveled up (had 90, gains 100+)
        assert result["A"]["leveled_up"] is True
        assert result["A"]["new_level"] >= 2


# ---------------------------------------------------------------------------
# Cycle 3: inject_xp_into_match wires xp_awards into match result
# ---------------------------------------------------------------------------


class TestInjectXpIntoMatch:
    def test_adds_xp_awards_field(self, db_conn: sqlite3.Connection) -> None:
        """inject_xp_into_match adds 'xp_awards' key to match_data."""
        from engine.xp_runner import inject_xp_into_match

        match = _minimal_match()
        inject_xp_into_match(match, db_conn)
        assert "xp_awards" in match

    def test_xp_awards_has_all_players(self, db_conn: sqlite3.Connection) -> None:
        """xp_awards dict has entries for all players."""
        from engine.xp_runner import inject_xp_into_match

        match = _minimal_match()
        inject_xp_into_match(match, db_conn)
        assert set(match["xp_awards"].keys()) == {"A", "B", "C"}

    def test_does_not_mutate_other_fields(self, db_conn: sqlite3.Connection) -> None:
        """inject_xp_into_match preserves existing match data fields."""
        from engine.xp_runner import inject_xp_into_match

        match = _minimal_match()
        original_winner = match["winner"]
        original_stats = dict(match["stats"])
        inject_xp_into_match(match, db_conn)
        assert match["winner"] == original_winner
        assert match["stats"] == original_stats

    def test_skipped_when_no_xp_true(self, db_conn: sqlite3.Connection) -> None:
        """When no_xp=True, xp_awards is NOT added."""
        from engine.xp_runner import inject_xp_into_match

        match = _minimal_match()
        inject_xp_into_match(match, db_conn, no_xp=True)
        assert "xp_awards" not in match


# ---------------------------------------------------------------------------
# Cycle 4: Auto-create DB from path
# ---------------------------------------------------------------------------


class TestAutoCreateDb:
    def test_creates_db_file(self, tmp_path) -> None:
        """inject_xp_into_match auto-creates the DB at the given path."""
        from engine.xp_runner import inject_xp_into_match

        db_path = str(tmp_path / "profiles.db")
        match = _minimal_match()
        # Pass db_path instead of conn -- uses path-based overload
        inject_xp_into_match(match, db_path=db_path)
        assert (tmp_path / "profiles.db").exists()

    def test_creates_parent_dir(self, tmp_path) -> None:
        """Auto-creates parent directory for the DB file."""
        from engine.xp_runner import inject_xp_into_match

        db_path = str(tmp_path / "subdir" / "profiles.db")
        match = _minimal_match()
        inject_xp_into_match(match, db_path=db_path)
        assert (tmp_path / "subdir" / "profiles.db").exists()
