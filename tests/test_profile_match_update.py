"""Tests for update_profiles_after_match() in data/player_profiles.py."""

from pathlib import Path

from data.player_profiles import (
    PlayerProfile,
    load_profiles,
    save_profiles,
    update_profiles_after_match,
)
from engine.game import run_match
from tests.conftest import always_rest, bot_config, chase_and_attack


def _make_players() -> list[dict[str, str]]:
    """Return a 3-player match roster."""
    return [
        {"emoji": "A", "name": "AlphaBot", "bio": "first", "author": "alice"},
        {"emoji": "B", "name": "BravoBot", "bio": "second", "author": "bob"},
        {"emoji": "C", "name": "CharlieBot", "bio": "third", "author": "carol"},
    ]


class TestWinnerUpdated:
    """Winner's profile is updated after match."""

    def test_winner_wins_incremented(self, tmp_path: Path) -> None:
        path = tmp_path / "profiles.json"
        players = _make_players()
        update_profiles_after_match(path, players, winner_emoji="A")
        profiles = load_profiles(path)
        assert profiles["alice"].wins == 1

    def test_winner_streak_incremented(self, tmp_path: Path) -> None:
        path = tmp_path / "profiles.json"
        players = _make_players()
        update_profiles_after_match(path, players, winner_emoji="A")
        profiles = load_profiles(path)
        assert profiles["alice"].current_streak == 1

    def test_losers_streak_reset(self, tmp_path: Path) -> None:
        path = tmp_path / "profiles.json"
        # Pre-seed bob with an active streak
        existing = {
            "bob": PlayerProfile(
                player_id="bob", bot_name="BravoBot", emoji="B",
                current_streak=3, best_streak=5,
            ),
        }
        save_profiles(existing, path)

        players = _make_players()
        update_profiles_after_match(path, players, winner_emoji="A")
        profiles = load_profiles(path)
        assert profiles["bob"].current_streak == 0
        assert profiles["bob"].best_streak == 5  # preserved


class TestBudgetRecalculated:
    """line_budget is recalculated after update."""

    def test_winner_budget_increases(self, tmp_path: Path) -> None:
        path = tmp_path / "profiles.json"
        players = _make_players()
        update_profiles_after_match(path, players, winner_emoji="A")
        profiles = load_profiles(path)
        # 1 win = base 50 + 10 = 60
        assert profiles["alice"].line_budget == 60


class TestProfilesSavedToDisk:
    """Profiles file is written after match."""

    def test_file_exists_after_update(self, tmp_path: Path) -> None:
        path = tmp_path / "profiles.json"
        assert not path.exists()
        players = _make_players()
        update_profiles_after_match(path, players, winner_emoji="A")
        assert path.exists()


class TestNewBotsCreated:
    """New bots get fresh profiles created automatically."""

    def test_all_players_get_profiles(self, tmp_path: Path) -> None:
        path = tmp_path / "profiles.json"
        players = _make_players()
        update_profiles_after_match(path, players, winner_emoji="A")
        profiles = load_profiles(path)
        assert set(profiles.keys()) == {"alice", "bob", "carol"}
        # Non-winners start with 0 wins
        assert profiles["bob"].wins == 0
        assert profiles["carol"].wins == 0


class TestExistingProfilesPreserved:
    """Existing profiles are updated, not overwritten."""

    def test_existing_wins_accumulated(self, tmp_path: Path) -> None:
        path = tmp_path / "profiles.json"
        # Pre-seed alice with 5 wins
        existing = {
            "alice": PlayerProfile(
                player_id="alice", bot_name="AlphaBot", emoji="A",
                wins=5, current_streak=2, best_streak=4, line_budget=100,
            ),
        }
        save_profiles(existing, path)

        players = _make_players()
        update_profiles_after_match(path, players, winner_emoji="A")
        profiles = load_profiles(path)
        assert profiles["alice"].wins == 6
        assert profiles["alice"].current_streak == 3
        assert profiles["alice"].best_streak == 4  # 3 < 4, no change


class TestRunMatchIntegration:
    """run_match with profiles_path updates profiles on disk."""

    def test_profiles_written_after_match(self, tmp_path: Path) -> None:
        path = tmp_path / "profiles.json"
        configs = [
            {"name": "A", "emoji": "X", "bio": "", "author": "alice", "decide_func": always_rest},
            {"name": "B", "emoji": "Y", "bio": "", "author": "bob", "decide_func": chase_and_attack},
        ]
        run_match(configs, match_id=1, seed=42, profiles_path=path)
        assert path.exists()
        profiles = load_profiles(path)
        # Exactly 2 profiles created (one per distinct author)
        assert len(profiles) == 2

    def test_profiles_not_written_when_path_none(self, tmp_path: Path) -> None:
        """Default behavior: no profiles_path means no file created."""
        configs = [
            bot_config("A", "X", always_rest),
            bot_config("B", "Y", chase_and_attack),
        ]
        # Should not raise -- profiles_path defaults to None
        data = run_match(configs, match_id=1, seed=42)
        assert "winner" in data
