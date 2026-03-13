"""Tests for data/player_profiles.py — player profile schema and storage."""

from pathlib import Path

from data.player_profiles import (
    PlayerProfile,
    get_or_create_profile,
    load_profiles,
    save_profiles,
)


class TestPlayerProfileDefaults:
    """PlayerProfile created with correct defaults."""

    def test_defaults(self) -> None:
        p = PlayerProfile(player_id="p1", bot_name="TestBot", emoji="X")
        assert p.line_budget == 50
        assert p.wins == 0
        assert p.current_streak == 0
        assert p.best_streak == 0
        assert p.unlocked_actions == ["attack", "defend", "move", "rest"]
        assert p.watcher_encounters == 0
        assert p.watcher_wins == 0
        assert p.watcher_losses == 0

    def test_identity_fields(self) -> None:
        p = PlayerProfile(player_id="abc123", bot_name="GooseBot", emoji="G")
        assert p.player_id == "abc123"
        assert p.bot_name == "GooseBot"
        assert p.emoji == "G"

    def test_custom_values(self) -> None:
        p = PlayerProfile(
            player_id="p2",
            bot_name="VetBot",
            emoji="V",
            line_budget=80,
            wins=5,
            current_streak=3,
            best_streak=7,
            unlocked_actions=["move", "attack", "rest", "defend", "flee"],
            watcher_encounters=2,
            watcher_wins=1,
            watcher_losses=1,
        )
        assert p.wins == 5
        assert p.best_streak == 7
        assert p.unlocked_actions == ["move", "attack", "rest", "defend", "flee"]


class TestLoadSaveRoundtrip:
    """load_profiles / save_profiles roundtrip preserves all fields."""

    def test_roundtrip(self, tmp_path: Path) -> None:
        path = tmp_path / "profiles.json"
        profiles = {
            "p1": PlayerProfile(
                player_id="p1",
                bot_name="Bot1",
                emoji="A",
                wins=3,
                current_streak=2,
                best_streak=5,
                watcher_encounters=1,
            ),
            "p2": PlayerProfile(player_id="p2", bot_name="Bot2", emoji="B"),
        }
        save_profiles(profiles, path)
        loaded = load_profiles(path)
        assert loaded["p1"].wins == 3
        assert loaded["p1"].current_streak == 2
        assert loaded["p1"].best_streak == 5
        assert loaded["p1"].watcher_encounters == 1
        assert loaded["p1"].bot_name == "Bot1"
        assert loaded["p1"].emoji == "A"
        assert loaded["p2"].bot_name == "Bot2"
        assert loaded["p2"].unlocked_actions == ["attack", "defend", "move", "rest"]

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        path = tmp_path / "nested" / "deep" / "profiles.json"
        profiles = {"p1": PlayerProfile(player_id="p1", bot_name="B", emoji="X")}
        save_profiles(profiles, path)
        assert path.exists()


class TestLoadMissingFile:
    """load_profiles on missing file returns empty dict."""

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "nonexistent.json"
        result = load_profiles(path)
        assert result == {}

    def test_corrupt_json_returns_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{invalid json!!")
        result = load_profiles(path)
        assert result == {}


class TestGetOrCreateProfile:
    """get_or_create_profile returns existing or creates new."""

    def test_returns_existing(self) -> None:
        existing = PlayerProfile(
            player_id="p1", bot_name="OldName", emoji="O", wins=10
        )
        profiles: dict[str, PlayerProfile] = {"p1": existing}
        result = get_or_create_profile(profiles, "p1", "NewName", "N")
        assert result is existing
        assert result.wins == 10
        assert result.bot_name == "OldName"

    def test_creates_new_with_defaults(self) -> None:
        profiles: dict[str, PlayerProfile] = {}
        result = get_or_create_profile(profiles, "p1", "Fresh", "F")
        assert result.player_id == "p1"
        assert result.bot_name == "Fresh"
        assert result.emoji == "F"
        assert result.wins == 0
        assert result.line_budget == 50
        assert "p1" in profiles

    def test_does_not_overwrite_existing(self) -> None:
        profiles: dict[str, PlayerProfile] = {
            "p1": PlayerProfile(player_id="p1", bot_name="A", emoji="X", wins=5)
        }
        get_or_create_profile(profiles, "p1", "B", "Y")
        assert profiles["p1"].bot_name == "A"
        assert profiles["p1"].wins == 5
