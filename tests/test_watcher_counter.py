"""Tests for The Watcher's counter-action selection engine."""

from __future__ import annotations

from engine.watcher_brain import COUNTER_MAP, select_counter_action
from engine.watcher_memory import CONTEXTS, PatternTable


def _seeded_table(player_id: str, context: str, action: str, count: int = 10) -> PatternTable:
    """Build a PatternTable with a dominant action for a player+context."""
    table = PatternTable()
    for _ in range(count):
        table.record(player_id, context, action)
    return table


# --- Cycle 1: move -> intercept ---


def test_counter_map_has_move():
    assert "move" in COUNTER_MAP
    assert COUNTER_MAP["move"] == "move"  # intercept = move toward


def test_predicted_move_returns_move_toward_target():
    """When human is predicted to move, Watcher intercepts (moves toward)."""
    table = _seeded_table("p1", "after_damage", "move")
    result = select_counter_action(
        pattern_table=table,
        target_id="p1",
        watcher_x=0, watcher_y=0,
        target_x=3, target_y=1,
        contexts=CONTEXTS,
        all_actions={"move", "attack", "rest", "defend", "ranged_attack", "dash", "taunt"},
    )
    # Should move east (toward target at 3,1 from 0,0 — dx=3 > dy=1)
    assert result == ("move", "east")


# --- Cycle 2: attack -> defend, rest -> rush ---


ALL_ACTIONS = {"move", "attack", "rest", "defend", "ranged_attack", "dash", "taunt"}


def test_predicted_attack_returns_defend():
    """When human is predicted to attack, Watcher defends."""
    table = _seeded_table("p1", "at_range_1", "attack")
    result = select_counter_action(
        pattern_table=table,
        target_id="p1",
        watcher_x=5, watcher_y=5,
        target_x=5, target_y=4,
        contexts=CONTEXTS,
        all_actions=ALL_ACTIONS,
    )
    assert result == ("defend",)


def test_predicted_rest_returns_rush():
    """When human is predicted to rest, Watcher rushes (moves toward)."""
    table = _seeded_table("p1", "below_30_hp", "rest")
    result = select_counter_action(
        pattern_table=table,
        target_id="p1",
        watcher_x=0, watcher_y=5,
        target_x=0, target_y=0,
        contexts=CONTEXTS,
        all_actions=ALL_ACTIONS,
    )
    # rush = move toward; target is north (dy=-5)
    assert result == ("move", "north")


# --- Cycle 3: defend -> ranged_attack, ranged_attack -> dash, dash -> taunt ---


def test_predicted_defend_returns_ranged_attack():
    """When human is predicted to defend, Watcher uses ranged_attack."""
    table = _seeded_table("p1", "storm_closing", "defend")
    result = select_counter_action(
        pattern_table=table,
        target_id="p1",
        watcher_x=5, watcher_y=5,
        target_x=2, target_y=5,
        contexts=CONTEXTS,
        all_actions=ALL_ACTIONS,
    )
    # ranged_attack toward west (dx=-3)
    assert result == ("ranged_attack", "west")


def test_predicted_ranged_attack_returns_dash():
    """When human is predicted to ranged_attack, Watcher dashes to close distance."""
    table = _seeded_table("p1", "after_damage", "ranged_attack")
    result = select_counter_action(
        pattern_table=table,
        target_id="p1",
        watcher_x=2, watcher_y=2,
        target_x=2, target_y=8,
        contexts=CONTEXTS,
        all_actions=ALL_ACTIONS,
    )
    # dash south toward target
    assert result == ("dash", "south")


def test_predicted_dash_returns_taunt():
    """When human is predicted to dash, Watcher taunts."""
    table = _seeded_table("p1", "override_detected", "dash")
    result = select_counter_action(
        pattern_table=table,
        target_id="p1",
        watcher_x=5, watcher_y=5,
        target_x=8, target_y=5,
        contexts=CONTEXTS,
        all_actions=ALL_ACTIONS,
    )
    assert result == ("taunt",)


# --- Cycle 4: global fallback, valid tuple, highest confidence ---


def test_falls_back_to_global_when_no_player_data():
    """When target has no data, uses __global__ profile."""
    table = PatternTable()
    # Only global data: record under a different player so global gets populated
    for _ in range(10):
        table.record("other_player", "after_damage", "defend")

    result = select_counter_action(
        pattern_table=table,
        target_id="unknown_player",
        watcher_x=0, watcher_y=0,
        target_x=5, target_y=0,
        contexts=CONTEXTS,
        all_actions=ALL_ACTIONS,
    )
    # Global predicts "defend" -> counter is ranged_attack toward east
    assert result == ("ranged_attack", "east")


def test_returns_valid_action_tuple():
    """Return value is always a tuple of strings."""
    table = _seeded_table("p1", "at_range_1", "move")
    result = select_counter_action(
        pattern_table=table,
        target_id="p1",
        watcher_x=0, watcher_y=0,
        target_x=1, target_y=0,
        contexts=CONTEXTS,
        all_actions=ALL_ACTIONS,
    )
    assert isinstance(result, tuple)
    assert all(isinstance(s, str) for s in result)
    assert len(result) >= 1


def test_picks_highest_confidence_context():
    """When multiple contexts have data, uses the one with highest confidence."""
    table = PatternTable()
    # Low confidence: after_damage has mixed actions
    for _ in range(5):
        table.record("p1", "after_damage", "move")
    for _ in range(4):
        table.record("p1", "after_damage", "attack")
    # High confidence: at_range_1 is 100% defend
    for _ in range(10):
        table.record("p1", "at_range_1", "defend")

    result = select_counter_action(
        pattern_table=table,
        target_id="p1",
        watcher_x=5, watcher_y=5,
        target_x=8, target_y=5,
        contexts=CONTEXTS,
        all_actions=ALL_ACTIONS,
    )
    # at_range_1 predicts "defend" with 100% confidence -> ranged_attack east
    assert result == ("ranged_attack", "east")


def test_no_data_at_all_defaults_to_move():
    """When no data exists for anyone, falls back to move toward target."""
    table = PatternTable()
    result = select_counter_action(
        pattern_table=table,
        target_id="p1",
        watcher_x=3, watcher_y=3,
        target_x=3, target_y=0,
        contexts=CONTEXTS,
        all_actions=ALL_ACTIONS,
    )
    # Default predicted action is "move", counter is "move" toward north
    assert result == ("move", "north")


def test_counter_action_unavailable_falls_back_to_move():
    """When counter action not in all_actions, falls back to move."""
    table = _seeded_table("p1", "at_range_1", "defend")
    # Exclude ranged_attack from available actions
    limited_actions = {"move", "attack", "rest", "defend"}
    result = select_counter_action(
        pattern_table=table,
        target_id="p1",
        watcher_x=0, watcher_y=0,
        target_x=5, target_y=0,
        contexts=CONTEXTS,
        all_actions=limited_actions,
    )
    # Counter for defend is ranged_attack, but not available -> fallback to move east
    assert result == ("move", "east")
