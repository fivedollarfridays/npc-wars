"""Tests for Watcher lifetime stats and kill/death tracking."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.watcher_stats import (
    WatcherStats,
    load_stats,
    save_stats,
)


class TestWatcherStatsInit:
    """WatcherStats initializes with all counters at zero."""

    def test_defaults_zero(self) -> None:
        stats = WatcherStats()
        assert stats.matches == 0
        assert stats.wins == 0
        assert stats.kills == 0
        assert stats.human_kills == 0
        assert stats.bot_kills == 0
        assert stats.deaths == 0
        assert stats.current_streak == 0
        assert stats.encounters == {}


class TestRecordKill:
    """record_kill increments the correct counters."""

    def test_human_kill(self) -> None:
        stats = WatcherStats()
        stats.record_kill("human")
        assert stats.kills == 1
        assert stats.human_kills == 1
        assert stats.bot_kills == 0

    def test_bot_kill(self) -> None:
        stats = WatcherStats()
        stats.record_kill("bot")
        assert stats.kills == 1
        assert stats.bot_kills == 1
        assert stats.human_kills == 0

    def test_default_is_bot(self) -> None:
        stats = WatcherStats()
        stats.record_kill()
        assert stats.bot_kills == 1

    def test_multiple_kills(self) -> None:
        stats = WatcherStats()
        stats.record_kill("human")
        stats.record_kill("bot")
        stats.record_kill("human")
        assert stats.kills == 3
        assert stats.human_kills == 2
        assert stats.bot_kills == 1


class TestRecordDeath:
    """record_death increments deaths."""

    def test_single_death(self) -> None:
        stats = WatcherStats()
        stats.record_death()
        assert stats.deaths == 1

    def test_multiple_deaths(self) -> None:
        stats = WatcherStats()
        stats.record_death()
        stats.record_death()
        assert stats.deaths == 2


class TestRecordMatch:
    """record_match tracks matches, wins, and streak."""

    def test_win_increments_matches_and_wins(self) -> None:
        stats = WatcherStats()
        stats.record_match(won=True)
        assert stats.matches == 1
        assert stats.wins == 1

    def test_win_increments_streak(self) -> None:
        stats = WatcherStats()
        stats.record_match(won=True)
        stats.record_match(won=True)
        assert stats.current_streak == 2

    def test_loss_resets_streak(self) -> None:
        stats = WatcherStats()
        stats.record_match(won=True)
        stats.record_match(won=True)
        stats.record_match(won=False)
        assert stats.current_streak == 0
        assert stats.matches == 3
        assert stats.wins == 2

    def test_loss_increments_matches_not_wins(self) -> None:
        stats = WatcherStats()
        stats.record_match(won=False)
        assert stats.matches == 1
        assert stats.wins == 0


class TestWinRate:
    """win_rate property calculates correctly."""

    def test_no_matches_returns_zero(self) -> None:
        stats = WatcherStats()
        assert stats.win_rate == 0.0

    def test_all_wins(self) -> None:
        stats = WatcherStats()
        stats.record_match(won=True)
        stats.record_match(won=True)
        assert stats.win_rate == 1.0

    def test_mixed(self) -> None:
        stats = WatcherStats()
        stats.record_match(won=True)
        stats.record_match(won=False)
        assert stats.win_rate == pytest.approx(0.5)


class TestRecordEncounter:
    """record_encounter tracks per-player stats."""

    def test_new_player_win(self) -> None:
        stats = WatcherStats()
        stats.record_encounter("player_1", won=True)
        assert stats.encounters["player_1"] == {"count": 1, "wins": 1}

    def test_new_player_loss(self) -> None:
        stats = WatcherStats()
        stats.record_encounter("player_1", won=False)
        assert stats.encounters["player_1"] == {"count": 1, "wins": 0}

    def test_repeat_encounters(self) -> None:
        stats = WatcherStats()
        stats.record_encounter("p1", won=True)
        stats.record_encounter("p1", won=False)
        stats.record_encounter("p1", won=True)
        assert stats.encounters["p1"] == {"count": 3, "wins": 2}

    def test_multiple_players(self) -> None:
        stats = WatcherStats()
        stats.record_encounter("a", won=True)
        stats.record_encounter("b", won=False)
        assert "a" in stats.encounters
        assert "b" in stats.encounters


class TestSerialization:
    """to_dict / from_dict roundtrip preserves all data."""

    def test_empty_roundtrip(self) -> None:
        stats = WatcherStats()
        restored = WatcherStats.from_dict(stats.to_dict())
        assert restored.matches == 0
        assert restored.encounters == {}

    def test_full_roundtrip(self) -> None:
        stats = WatcherStats()
        stats.record_kill("human")
        stats.record_kill("bot")
        stats.record_death()
        stats.record_match(won=True)
        stats.record_match(won=True)
        stats.record_match(won=False)
        stats.record_encounter("p1", won=True)
        stats.record_encounter("p1", won=False)

        data = stats.to_dict()
        restored = WatcherStats.from_dict(data)

        assert restored.matches == 3
        assert restored.wins == 2
        assert restored.kills == 2
        assert restored.human_kills == 1
        assert restored.bot_kills == 1
        assert restored.deaths == 1
        assert restored.current_streak == 0
        assert restored.encounters == {"p1": {"count": 2, "wins": 1}}
        assert restored.win_rate == pytest.approx(2 / 3)


class TestPersistence:
    """save_stats / load_stats persist to JSON file."""

    def test_save_and_load(self, tmp_path: Path) -> None:
        path = str(tmp_path / "stats.json")
        stats = WatcherStats()
        stats.record_kill("human")
        stats.record_match(won=True)
        stats.record_encounter("p1", won=True)

        save_stats(stats, path)
        loaded = load_stats(path)

        assert loaded.kills == 1
        assert loaded.human_kills == 1
        assert loaded.matches == 1
        assert loaded.wins == 1
        assert loaded.encounters == {"p1": {"count": 1, "wins": 1}}

    def test_load_missing_file_returns_empty(self, tmp_path: Path) -> None:
        path = str(tmp_path / "nonexistent.json")
        loaded = load_stats(path)
        assert loaded.matches == 0
        assert loaded.encounters == {}

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        path = str(tmp_path / "sub" / "dir" / "stats.json")
        save_stats(WatcherStats(), path)
        assert Path(path).exists()

    def test_saved_file_is_valid_json(self, tmp_path: Path) -> None:
        path = str(tmp_path / "stats.json")
        save_stats(WatcherStats(), path)
        data = json.loads(Path(path).read_text())
        assert isinstance(data, dict)
