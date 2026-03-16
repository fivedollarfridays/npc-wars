"""E2E integration tests for diff data across two matches.

Runs two real matches using bots from bots/, verifies diff data is
correctly computed and persisted in the match JSON files.
"""

import json
import os

import pytest

from data.stat_diff import inject_diff_data
from engine.game import run_match
from engine.loader import load_bots
from engine.match_writer import write_match

BOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bots")

VALID_CLASSIFICATIONS = {"improved", "regressed", "neutral"}


@pytest.fixture()
def results_dir(tmp_path):
    """Isolated results directory for match output."""
    d = tmp_path / "results"
    d.mkdir()
    return str(d)


@pytest.fixture()
def bot_configs():
    """Load real bots from bots/ directory."""
    configs = load_bots(BOTS_DIR)
    assert len(configs) >= 2, "Need at least 2 bots in bots/"
    return configs


@pytest.fixture()
def two_matches(bot_configs, results_dir):
    """Run two matches, inject diffs, and write JSON. Return (match1, match2)."""
    match1 = run_match(bot_configs, match_id=1, seed=42)
    inject_diff_data(match1, results_dir)
    write_match(match1, results_dir)

    match2 = run_match(bot_configs, match_id=2, seed=99)
    inject_diff_data(match2, results_dir)
    write_match(match2, results_dir)

    return match1, match2


# ---- Cycle 1: First match diff (no history) ----


class TestFirstMatchDiff:
    """Match 1 should have first_match=True for all players (no history)."""

    def test_first_match_has_diff_with_first_match_flag(self, two_matches):
        """All players in match 1 have first_match=True in their diff."""
        match1, _match2 = two_matches
        assert "diff" in match1
        for emoji, player_diff in match1["diff"].items():
            assert player_diff.get("first_match") is True, (
                f"Player {emoji} in match 1 missing first_match=True"
            )

    def test_first_match_includes_current_values(self, two_matches):
        """First-match diff entries include 'current' values for each stat."""
        match1, _match2 = two_matches
        for emoji, player_diff in match1["diff"].items():
            stat_keys = [k for k in player_diff if k != "first_match"]
            assert len(stat_keys) > 0, f"Player {emoji} has no stat entries"
            for stat_key in stat_keys:
                entry = player_diff[stat_key]
                assert "current" in entry, (
                    f"Player {emoji} stat {stat_key} missing 'current'"
                )
                assert isinstance(entry["current"], (int, float))


# ---- Cycle 2: Second match has real diffs ----


class TestSecondMatchDiff:
    """Match 2 should have per-player diffs with classification/delta/percentage."""

    def test_second_match_has_real_diffs(self, two_matches):
        """Match 2 diff key exists with per-player entries."""
        _match1, match2 = two_matches
        assert "diff" in match2
        stats_emojis = set(match2["stats"].keys())
        diff_emojis = set(match2["diff"].keys())
        assert diff_emojis == stats_emojis

    def test_diff_classifications_are_valid(self, two_matches):
        """All classifications are 'improved', 'regressed', or 'neutral'."""
        _match1, match2 = two_matches
        for emoji, player_diff in match2["diff"].items():
            # Skip first_match sentinels (shouldn't appear in match 2)
            if player_diff.get("first_match"):
                continue
            for stat_key, entry in player_diff.items():
                assert entry["classification"] in VALID_CLASSIFICATIONS, (
                    f"Player {emoji} stat {stat_key}: "
                    f"invalid classification {entry['classification']!r}"
                )

    def test_diff_deltas_are_numeric(self, two_matches):
        """All delta values are int or float."""
        _match1, match2 = two_matches
        for emoji, player_diff in match2["diff"].items():
            if player_diff.get("first_match"):
                continue
            for stat_key, entry in player_diff.items():
                assert isinstance(entry["delta"], (int, float)), (
                    f"Player {emoji} stat {stat_key}: "
                    f"delta is {type(entry['delta']).__name__}, expected numeric"
                )

    def test_diff_percentages_are_numeric(self, two_matches):
        """All percentage values are int or float."""
        _match1, match2 = two_matches
        for emoji, player_diff in match2["diff"].items():
            if player_diff.get("first_match"):
                continue
            for stat_key, entry in player_diff.items():
                assert isinstance(entry["percentage"], (int, float, type(None))), (
                    f"Player {emoji} stat {stat_key}: "
                    f"percentage is {type(entry['percentage']).__name__}"
                )


# ---- Cycle 3: JSON persistence ----


class TestDiffPersistence:
    """Diff data survives JSON serialization to disk."""

    def test_diff_data_persists_in_json(self, two_matches, results_dir):
        """Load written JSON from disk, verify diff key survives serialization."""
        _match1, match2 = two_matches
        filepath = os.path.join(results_dir, "match_002.json")
        assert os.path.exists(filepath), "Match 2 JSON not written"

        with open(filepath, encoding="utf-8") as f:
            loaded = json.load(f)

        assert "diff" in loaded
        # Same players in memory and on disk
        assert set(loaded["diff"].keys()) == set(match2["diff"].keys())

        # Spot-check a player's diff structure
        for emoji in loaded["diff"]:
            disk_diff = loaded["diff"][emoji]
            mem_diff = match2["diff"][emoji]
            if disk_diff.get("first_match"):
                assert mem_diff.get("first_match") is True
            else:
                for stat_key in disk_diff:
                    assert disk_diff[stat_key]["classification"] == mem_diff[stat_key]["classification"]
                    assert disk_diff[stat_key]["delta"] == mem_diff[stat_key]["delta"]

    def test_first_match_json_also_persists(self, two_matches, results_dir):
        """Match 1 diff with first_match flag persists to disk."""
        match1, _match2 = two_matches
        filepath = os.path.join(results_dir, "match_001.json")
        assert os.path.exists(filepath)

        with open(filepath, encoding="utf-8") as f:
            loaded = json.load(f)

        assert "diff" in loaded
        for emoji, player_diff in loaded["diff"].items():
            assert player_diff.get("first_match") is True
