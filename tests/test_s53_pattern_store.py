"""Tests for per-player pattern persistence (T53.1)."""

from __future__ import annotations

import json

import pytest
from pathlib import Path


@pytest.fixture
def patterns_dir(tmp_path: Path) -> Path:
    """Use tmp_path as pattern storage directory."""
    return tmp_path


def _pos(
    emoji: str, x: int, y: int, hp: int, energy: int, action: str,
) -> dict:
    """Build a position dict for test match data."""
    return {
        "emoji": emoji, "x": x, "y": y, "hp": hp,
        "energy": energy, "action": action, "alive": True, "max_hp": 100,
    }


def _mock_match(
    player_emoji: str = "\U0001f916", rival_emoji: str = "\U0001f3af",
) -> dict:
    """Build minimal match data with 3 rounds for testing."""
    pe, re = player_emoji, rival_emoji
    return {
        "match_id": 1,
        "grid_size": 10,
        "rounds": [
            {
                "round": 1, "storm_border": 0,
                "positions": [
                    _pos(pe, 5, 5, 100, 80, "rest"),
                    _pos(re, 6, 5, 100, 100, "attack west"),
                ],
                "events": [
                    {"type": "hit", "source": re, "target": pe, "damage": 25},
                ],
            },
            {
                "round": 2, "storm_border": 0,
                "positions": [
                    _pos(pe, 5, 5, 75, 100, "attack east"),
                    _pos(re, 6, 5, 100, 90, "defend"),
                ],
                "events": [],
            },
            {
                "round": 3, "storm_border": 0,
                "positions": [
                    _pos(pe, 4, 5, 60, 70, "move west"),
                    _pos(re, 6, 5, 100, 80, "move west"),
                ],
                "events": [],
            },
        ],
        "eliminations": [],
        "winner": rival_emoji,
        "stats": {},
    }


# --- Cycle 1: load/save roundtrip ---


def test_load_empty_returns_empty_table(patterns_dir: Path) -> None:
    from server.rival_patterns import load_player_patterns
    from engine.watcher_memory import PatternTable

    table = load_player_patterns("nonexistent", base_dir=str(patterns_dir))
    assert isinstance(table, PatternTable)


def test_save_load_roundtrip(patterns_dir: Path) -> None:
    from server.rival_patterns import load_player_patterns, save_player_patterns
    from engine.watcher_memory import PatternTable

    table = PatternTable()
    table.record("p1", "at_range_1", "attack")
    table.record("p1", "at_range_1", "attack")
    table.record("p1", "at_range_1", "rest")
    save_player_patterns("p1", table, base_dir=str(patterns_dir))
    loaded = load_player_patterns("p1", base_dir=str(patterns_dir))
    counts = loaded.get_raw_counts("p1", "at_range_1")
    assert counts["attack"] == 2
    assert counts["rest"] == 1


def test_save_creates_directory(tmp_path: Path) -> None:
    from server.rival_patterns import save_player_patterns
    from engine.watcher_memory import PatternTable

    nested = tmp_path / "deep" / "nested"
    table = PatternTable()
    table.record("p1", "at_range_1", "attack")
    save_player_patterns("p1", table, base_dir=str(nested))
    assert (nested / "p1.json").exists()


# --- Cycle 2: record_match_patterns ---


def test_record_match_patterns_returns_table(patterns_dir: Path) -> None:
    from server.rival_patterns import record_match_patterns
    from engine.watcher_memory import PatternTable

    match = _mock_match()
    table = record_match_patterns("p1", match, "\U0001f916", base_dir=str(patterns_dir))
    assert isinstance(table, PatternTable)


def test_record_match_detects_at_range_1(patterns_dir: Path) -> None:
    from server.rival_patterns import record_match_patterns

    match = _mock_match()
    # Round 1 and 2: player at (5,5), rival at (6,5) -> distance 1
    table = record_match_patterns("p1", match, "\U0001f916", base_dir=str(patterns_dir))
    counts = table.get_raw_counts("p1", "at_range_1")
    assert counts.get("rest", 0) >= 1  # Round 1: rest while adjacent
    assert counts.get("attack", 0) >= 1  # Round 2: attack while adjacent


def test_record_match_detects_after_damage(patterns_dir: Path) -> None:
    from server.rival_patterns import record_match_patterns

    match = _mock_match()
    # Round 1 has a hit event targeting player
    table = record_match_patterns("p1", match, "\U0001f916", base_dir=str(patterns_dir))
    counts = table.get_raw_counts("p1", "after_damage")
    assert counts.get("rest", 0) >= 1  # Round 1: rest after being hit


def test_record_match_persists_to_disk(patterns_dir: Path) -> None:
    from server.rival_patterns import record_match_patterns, load_player_patterns

    match = _mock_match()
    record_match_patterns("p1", match, "\U0001f916", base_dir=str(patterns_dir))
    loaded = load_player_patterns("p1", base_dir=str(patterns_dir))
    # Should have at least some recorded data
    assert loaded.get_raw_counts("p1", "at_range_1")


def test_record_match_skips_dead_player(patterns_dir: Path) -> None:
    from server.rival_patterns import record_match_patterns

    match = _mock_match()
    match["rounds"][2]["positions"][0]["alive"] = False
    table = record_match_patterns("p1", match, "\U0001f916", base_dir=str(patterns_dir))
    # Round 3 should be skipped; only rounds 1 and 2 counted for at_range_1
    counts = table.get_raw_counts("p1", "at_range_1")
    assert "move" not in counts


# --- Cycle 3: get_pattern_summary ---


def test_get_pattern_summary_structure(patterns_dir: Path) -> None:
    from server.rival_patterns import record_match_patterns, get_pattern_summary

    match = _mock_match()
    table = record_match_patterns("p1", match, "\U0001f916", base_dir=str(patterns_dir))
    summary = get_pattern_summary(table, "p1")
    assert isinstance(summary, dict)
    for ctx, actions in summary.items():
        assert isinstance(actions, dict)
        for action, prob in actions.items():
            assert 0.0 <= prob <= 1.0


def test_get_pattern_summary_probabilities_sum_to_one(patterns_dir: Path) -> None:
    from server.rival_patterns import get_pattern_summary
    from engine.watcher_memory import PatternTable

    table = PatternTable()
    table.record("p1", "at_range_1", "attack")
    table.record("p1", "at_range_1", "attack")
    table.record("p1", "at_range_1", "rest")
    summary = get_pattern_summary(table, "p1")
    total = sum(summary["at_range_1"].values())
    assert abs(total - 1.0) < 0.001


# --- Cycle 4: compact_for_embed ---


def test_compact_for_embed_limits_contexts() -> None:
    from server.rival_patterns import compact_for_embed

    summary = {
        "at_range_1": {"attack": 0.6, "rest": 0.3, "move": 0.05, "defend": 0.05},
        "below_30_hp": {"rest": 0.8, "move": 0.1, "defend": 0.1},
        "after_damage": {"attack": 0.4, "rest": 0.3, "move": 0.2, "defend": 0.1},
    }
    compact = compact_for_embed(summary, max_contexts=2)
    assert len(compact) <= 2


def test_compact_for_embed_limits_actions() -> None:
    from server.rival_patterns import compact_for_embed

    summary = {
        "at_range_1": {"attack": 0.4, "rest": 0.3, "move": 0.15, "defend": 0.1, "heal": 0.05},
    }
    compact = compact_for_embed(summary, max_contexts=5)
    for ctx, actions in compact.items():
        assert len(actions) <= 3


def test_compact_size_limit() -> None:
    from server.rival_patterns import compact_for_embed

    summary = {f"ctx_{i}": {f"action_{j}": 0.1 for j in range(10)} for i in range(20)}
    compact = compact_for_embed(summary, max_contexts=5)
    serialized = json.dumps(compact)
    assert len(serialized) < 5000


def test_compact_empty_summary() -> None:
    from server.rival_patterns import compact_for_embed

    compact = compact_for_embed({}, max_contexts=5)
    assert compact == {}
