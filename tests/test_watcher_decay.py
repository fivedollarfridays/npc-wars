"""Tests for learning decay in watcher memory."""

from __future__ import annotations

from engine.watcher_memory import (
    CROSS_SESSION_RETENTION,
    GLOBAL_PROFILE,
    SESSION_RETENTION,
    PatternTable,
    decay_memory,
)


def _make_table() -> PatternTable:
    """Build a PatternTable with known counts for testing."""
    pt = PatternTable()
    # Record 10 attacks and 5 moves for player_a in after_damage context
    for _ in range(10):
        pt.record("player_a", "after_damage", "attack")
    for _ in range(5):
        pt.record("player_a", "after_damage", "move")
    return pt


# --- Constants ---


def test_session_retention_value() -> None:
    assert SESSION_RETENTION == 0.7


def test_cross_session_retention_value() -> None:
    assert CROSS_SESSION_RETENTION == 0.3


# --- Session decay (retention_rate=0.7) ---


def test_session_decay_multiplies_player_counts() -> None:
    pt = _make_table()
    decay_memory(pt, retention_rate=0.7)
    counts = pt.get_raw_counts("player_a", "after_damage")
    assert counts["attack"] == 10 * 0.7
    assert counts["move"] == 5 * 0.7


def test_session_decay_leaves_global_unchanged() -> None:
    pt = _make_table()
    global_before = pt.get_raw_counts(GLOBAL_PROFILE, "after_damage")
    decay_memory(pt, retention_rate=0.7)
    global_after = pt.get_raw_counts(GLOBAL_PROFILE, "after_damage")
    assert global_after == global_before


# --- Cross-session decay (retention_rate=0.3) ---


def test_cross_session_decay_multiplies_player_counts() -> None:
    pt = _make_table()
    decay_memory(pt, retention_rate=0.3)
    counts = pt.get_raw_counts("player_a", "after_damage")
    assert counts["attack"] == 10 * 0.3
    assert counts["move"] == 5 * 0.3


def test_cross_session_decay_leaves_global_unchanged() -> None:
    pt = _make_table()
    global_before = pt.get_raw_counts(GLOBAL_PROFILE, "after_damage")
    decay_memory(pt, retention_rate=0.3)
    global_after = pt.get_raw_counts(GLOBAL_PROFILE, "after_damage")
    assert global_after == global_before


# --- Edge cases ---


def test_retention_rate_one_leaves_data_unchanged() -> None:
    pt = _make_table()
    before = pt.to_dict()
    decay_memory(pt, retention_rate=1.0)
    after = pt.to_dict()
    assert after == before


def test_retention_rate_zero_zeros_player_data() -> None:
    pt = _make_table()
    decay_memory(pt, retention_rate=0.0)
    counts = pt.get_raw_counts("player_a", "after_damage")
    assert counts["attack"] == 0.0
    assert counts["move"] == 0.0


def test_retention_rate_zero_leaves_global_unchanged() -> None:
    pt = _make_table()
    global_before = pt.get_raw_counts(GLOBAL_PROFILE, "after_damage")
    decay_memory(pt, retention_rate=0.0)
    global_after = pt.get_raw_counts(GLOBAL_PROFILE, "after_damage")
    assert global_after == global_before


# --- Float preservation ---


def test_decayed_counts_are_floats() -> None:
    pt = PatternTable()
    for _ in range(3):
        pt.record("player_b", "at_range_1", "defend")
    decay_memory(pt, retention_rate=0.7)
    counts = pt.get_raw_counts("player_b", "at_range_1")
    # 3 * 0.7 = 2.1, must stay as float
    assert counts["defend"] == 3 * 0.7
    assert isinstance(counts["defend"], float)


def test_multiple_players_decayed_independently() -> None:
    pt = PatternTable()
    for _ in range(4):
        pt.record("p1", "after_damage", "attack")
    for _ in range(6):
        pt.record("p2", "after_damage", "move")
    decay_memory(pt, retention_rate=0.5)
    assert pt.get_raw_counts("p1", "after_damage")["attack"] == 2.0
    assert pt.get_raw_counts("p2", "after_damage")["move"] == 3.0


def test_decay_is_in_place_mutation() -> None:
    pt = _make_table()
    result = decay_memory(pt, retention_rate=0.7)
    assert result is None
    # Verify the original object was mutated
    counts = pt.get_raw_counts("player_a", "after_damage")
    assert counts["attack"] == 7.0
