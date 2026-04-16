"""Tests for Watcher dossier generation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.watcher_dossier import build_dossier, format_dossier_text


@pytest.fixture()
def patterns_dir(tmp_path: Path) -> Path:
    d = tmp_path / "patterns"
    d.mkdir()
    return d


@pytest.fixture()
def stats_path(tmp_path: Path) -> Path:
    return tmp_path / "watcher_stats.json"


def _write_patterns(
    patterns_dir: Path, player_id: str, data: dict,
) -> None:
    (patterns_dir / f"{player_id}.json").write_text(json.dumps(data))


def _write_stats(stats_path: Path, data: dict) -> None:
    stats_path.write_text(json.dumps(data))


class TestBuildDossierNoData:
    """Returns intro dossier for players with no history."""

    def test_no_pattern_file(
        self, patterns_dir: Path, stats_path: Path,
    ) -> None:
        result = build_dossier("unknown", str(patterns_dir), str(stats_path))
        assert result["player_id"] == "unknown"
        assert result["sync_score"] == 0.0
        assert result["predictions"] == []
        assert result["predictability_change"] == 0.0
        assert isinstance(result["text_summary"], str)
        assert len(result["text_summary"]) > 0

    def test_empty_pattern_table(
        self, patterns_dir: Path, stats_path: Path,
    ) -> None:
        _write_patterns(patterns_dir, "p1", {})
        result = build_dossier("p1", str(patterns_dir), str(stats_path))
        assert result["predictions"] == []
        assert result["sync_score"] == 0.0


class TestBuildDossierOneMatch:
    """Dossier from a single match with minimal data."""

    def test_single_context(
        self, patterns_dir: Path, stats_path: Path,
    ) -> None:
        _write_patterns(patterns_dir, "p1", {
            "p1": {"below_30_hp": {"rest": 3, "attack": 1}},
        })
        _write_stats(stats_path, {
            "matches": 1, "wins": 0, "kills": 0, "human_kills": 0,
            "bot_kills": 0, "deaths": 1, "current_streak": 0,
            "encounters": {"p1": {"count": 1, "wins": 0}},
        })
        result = build_dossier("p1", str(patterns_dir), str(stats_path))
        assert len(result["predictions"]) == 1
        pred = result["predictions"][0]
        assert pred["context"] == "below_30_hp"
        assert len(pred["actions"]) <= 3
        assert pred["actions"][0]["action"] == "rest"
        assert pred["actions"][0]["probability"] == pytest.approx(0.75)
        assert pred["counter"] is not None
        assert result["sync_score"] > 0.0


class TestBuildDossierMultipleMatches:
    """Dossier from 5+ matches with rich pattern data."""

    def test_multiple_contexts_sorted(
        self, patterns_dir: Path, stats_path: Path,
    ) -> None:
        _write_patterns(patterns_dir, "p1", {
            "p1": {
                "below_30_hp": {"rest": 10, "attack": 2},
                "at_range_1": {"attack": 8, "rest": 3, "move": 1},
                "after_damage": {"rest": 5, "move": 5},
                "storm_closing": {"move": 7, "rest": 1},
            },
        })
        _write_stats(stats_path, {
            "matches": 6, "wins": 2, "kills": 5, "human_kills": 2,
            "bot_kills": 3, "deaths": 4, "current_streak": 0,
            "encounters": {"p1": {"count": 6, "wins": 2}},
        })
        result = build_dossier("p1", str(patterns_dir), str(stats_path))
        assert len(result["predictions"]) >= 2
        # Each prediction has top 3 actions max
        for pred in result["predictions"]:
            assert len(pred["actions"]) <= 3
            assert all("action" in a and "probability" in a for a in pred["actions"])
            assert pred["counter"] is not None

    def test_high_sync_score(
        self, patterns_dir: Path, stats_path: Path,
    ) -> None:
        _write_patterns(patterns_dir, "p1", {
            "p1": {
                "below_30_hp": {"rest": 50},
                "at_range_1": {"attack": 40},
                "after_damage": {"rest": 30},
            },
        })
        _write_stats(stats_path, {
            "matches": 10, "wins": 5, "kills": 10, "human_kills": 5,
            "bot_kills": 5, "deaths": 5, "current_streak": 0,
            "encounters": {"p1": {"count": 10, "wins": 5}},
        })
        result = build_dossier("p1", str(patterns_dir), str(stats_path))
        assert result["sync_score"] > 50.0

    def test_low_sync_score_few_observations(
        self, patterns_dir: Path, stats_path: Path,
    ) -> None:
        _write_patterns(patterns_dir, "p1", {
            "p1": {"below_30_hp": {"rest": 1}},
        })
        result = build_dossier("p1", str(patterns_dir), str(stats_path))
        assert result["sync_score"] < 30.0


class TestPredictabilityChange:
    """Predictability change reflects how concentrated patterns are."""

    def test_highly_predictable(
        self, patterns_dir: Path, stats_path: Path,
    ) -> None:
        _write_patterns(patterns_dir, "p1", {
            "p1": {"below_30_hp": {"rest": 20}},
        })
        result = build_dossier("p1", str(patterns_dir), str(stats_path))
        # Single action = 100% predictable
        assert result["predictability_change"] >= 0.9

    def test_unpredictable(
        self, patterns_dir: Path, stats_path: Path,
    ) -> None:
        _write_patterns(patterns_dir, "p1", {
            "p1": {"below_30_hp": {"rest": 5, "attack": 5, "move": 5}},
        })
        result = build_dossier("p1", str(patterns_dir), str(stats_path))
        # Evenly distributed = low predictability
        assert result["predictability_change"] < 0.5


class TestFormatDossierText:
    """Human-readable text summary generation."""

    def test_intro_dossier_text(self) -> None:
        dossier = {
            "player_id": "new_player",
            "sync_score": 0.0,
            "predictions": [],
            "predictability_change": 0.0,
        }
        text = format_dossier_text(dossier)
        assert "new_player" in text
        assert len(text) > 10

    def test_full_dossier_text(self) -> None:
        dossier = {
            "player_id": "veteran",
            "sync_score": 72.5,
            "predictions": [
                {
                    "context": "below_30_hp",
                    "actions": [
                        {"action": "rest", "probability": 0.78},
                        {"action": "attack", "probability": 0.15},
                    ],
                    "counter": "attack",
                },
            ],
            "predictability_change": 0.78,
        }
        text = format_dossier_text(dossier)
        assert "below_30_hp" in text
        assert "rest" in text
        assert "78" in text
        assert "72" in text or "72.5" in text
