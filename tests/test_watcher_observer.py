"""Tests for the watcher observer — classifies human action contexts."""

from __future__ import annotations

from engine.combat import Bot
from engine.watcher_memory import PatternTable
from engine.watcher_observer import classify_contexts, observe_round


def _make_bot(emoji: str, x: int = 5, y: int = 5, hp: int = 100) -> Bot:
    """Create a minimal bot for testing."""
    bot = Bot(
        name=f"bot_{emoji}",
        emoji=emoji,
        bio="test",
        author="test",
        decide_func=lambda **kw: ("rest",),
        x=x,
        y=y,
    )
    bot.hp = hp
    return bot


# --- classify_contexts tests ---


def test_after_damage_from_hit():
    human = _make_bot("H", x=3, y=3)
    enemy = _make_bot("E", x=8, y=8)
    bots = [human, enemy]
    events = [{"type": "hit", "attacker": "E", "target": "H", "damage": 10, "hp_before": 100}]
    actions = {"H": ("rest",)}

    result = classify_contexts("H", events, bots, storm_border=0, grid_size=10, actions=actions)
    assert "after_damage" in result


def test_after_damage_from_ranged_hit():
    human = _make_bot("H", x=3, y=3)
    enemy = _make_bot("E", x=8, y=8)
    bots = [human, enemy]
    events = [{"type": "ranged_hit", "attacker": "E", "target": "H", "damage": 5, "hp_before": 100}]
    actions = {"H": ("rest",)}

    result = classify_contexts("H", events, bots, storm_border=0, grid_size=10, actions=actions)
    assert "after_damage" in result


def test_no_after_damage_when_not_targeted():
    human = _make_bot("H", x=3, y=3)
    enemy = _make_bot("E", x=8, y=8)
    bots = [human, enemy]
    events = [{"type": "hit", "attacker": "H", "target": "E", "damage": 10, "hp_before": 100}]
    actions = {"H": ("rest",)}

    result = classify_contexts("H", events, bots, storm_border=0, grid_size=10, actions=actions)
    assert "after_damage" not in result


def test_at_range_1_manhattan_distance():
    human = _make_bot("H", x=3, y=3)
    enemy = _make_bot("E", x=3, y=4)  # Manhattan dist = 1
    bots = [human, enemy]
    actions = {"H": ("attack", "south")}

    result = classify_contexts("H", [], bots, storm_border=0, grid_size=10, actions=actions)
    assert "at_range_1" in result


def test_no_at_range_1_when_far():
    human = _make_bot("H", x=3, y=3)
    enemy = _make_bot("E", x=6, y=6)  # Manhattan dist = 6
    bots = [human, enemy]
    actions = {"H": ("rest",)}

    result = classify_contexts("H", [], bots, storm_border=0, grid_size=10, actions=actions)
    assert "at_range_1" not in result


def test_at_range_1_ignores_dead_enemies():
    human = _make_bot("H", x=3, y=3)
    enemy = _make_bot("E", x=3, y=4)
    enemy.alive = False
    bots = [human, enemy]
    actions = {"H": ("rest",)}

    result = classify_contexts("H", [], bots, storm_border=0, grid_size=10, actions=actions)
    assert "at_range_1" not in result


def test_below_30_hp():
    human = _make_bot("H", x=3, y=3, hp=29)
    bots = [human]
    actions = {"H": ("rest",)}

    result = classify_contexts("H", [], bots, storm_border=0, grid_size=10, actions=actions)
    assert "below_30_hp" in result


def test_not_below_30_hp_at_30():
    human = _make_bot("H", x=3, y=3, hp=30)
    bots = [human]
    actions = {"H": ("rest",)}

    result = classify_contexts("H", [], bots, storm_border=0, grid_size=10, actions=actions)
    assert "below_30_hp" not in result


def test_storm_closing_near_border():
    # storm_border=3 on grid_size=10 means safe zone is cols/rows 3..6
    # bot at x=1 is outside safe zone, within 2 tiles of border
    human = _make_bot("H", x=1, y=5)
    bots = [human]
    actions = {"H": ("move", "east")}

    result = classify_contexts("H", [], bots, storm_border=3, grid_size=10, actions=actions)
    assert "storm_closing" in result


def test_no_storm_closing_when_safe():
    # bot at center of a grid_size=10 with storm_border=1
    human = _make_bot("H", x=5, y=5)
    bots = [human]
    actions = {"H": ("rest",)}

    result = classify_contexts("H", [], bots, storm_border=1, grid_size=10, actions=actions)
    assert "storm_closing" not in result


def test_no_storm_closing_when_no_storm():
    human = _make_bot("H", x=0, y=0)
    bots = [human]
    actions = {"H": ("rest",)}

    result = classify_contexts("H", [], bots, storm_border=0, grid_size=10, actions=actions)
    assert "storm_closing" not in result


def test_override_detected():
    human = _make_bot("H", x=5, y=5)
    bots = [human]
    actions = {"H": ("attack", "north")}
    bot_decisions = {"H": ("rest",)}

    result = classify_contexts(
        "H", [], bots, storm_border=0, grid_size=10,
        actions=actions, bot_decisions=bot_decisions,
    )
    assert "override_detected" in result


def test_no_override_when_same_action():
    human = _make_bot("H", x=5, y=5)
    bots = [human]
    actions = {"H": ("rest",)}
    bot_decisions = {"H": ("rest",)}

    result = classify_contexts(
        "H", [], bots, storm_border=0, grid_size=10,
        actions=actions, bot_decisions=bot_decisions,
    )
    assert "override_detected" not in result


def test_no_override_without_bot_decisions():
    human = _make_bot("H", x=5, y=5)
    bots = [human]
    actions = {"H": ("attack", "north")}

    result = classify_contexts("H", [], bots, storm_border=0, grid_size=10, actions=actions)
    assert "override_detected" not in result


def test_multiple_contexts_same_round():
    """Human at low HP, adjacent to enemy, and just got hit => 3 contexts."""
    human = _make_bot("H", x=3, y=3, hp=20)
    enemy = _make_bot("E", x=3, y=4)  # Manhattan dist = 1
    bots = [human, enemy]
    events = [{"type": "hit", "attacker": "E", "target": "H", "damage": 10, "hp_before": 30}]
    actions = {"H": ("defend",)}

    result = classify_contexts("H", events, bots, storm_border=0, grid_size=10, actions=actions)
    assert "after_damage" in result
    assert "at_range_1" in result
    assert "below_30_hp" in result


def test_unknown_human_returns_empty():
    bots = [_make_bot("E", x=5, y=5)]
    result = classify_contexts("Z", [], bots, storm_border=0, grid_size=10, actions={})
    assert result == []


# --- observe_round tests ---


def test_observe_round_records_per_player_and_global():
    pt = PatternTable()
    human = _make_bot("H", x=3, y=3, hp=20)
    bots = [human]
    actions = {"H": ("rest",)}

    observe_round(pt, ["H"], [], bots, storm_border=0, grid_size=10, actions=actions)

    # below_30_hp triggers; action "rest" recorded for both H and __global__
    assert pt.get_raw_counts("H", "below_30_hp") == {"rest": 1}
    assert pt.get_raw_counts("__global__", "below_30_hp") == {"rest": 1}


def test_observe_round_multiple_humans():
    pt = PatternTable()
    h1 = _make_bot("A", x=3, y=3, hp=20)
    h2 = _make_bot("B", x=7, y=7, hp=25)
    bots = [h1, h2]
    actions = {"A": ("rest",), "B": ("move", "north")}

    observe_round(pt, ["A", "B"], [], bots, storm_border=0, grid_size=10, actions=actions)

    assert pt.get_raw_counts("A", "below_30_hp") == {"rest": 1}
    assert pt.get_raw_counts("B", "below_30_hp") == {"move": 1}


def test_observe_round_no_context_no_record():
    """Human in safe conditions => no contexts => no records."""
    pt = PatternTable()
    human = _make_bot("H", x=5, y=5, hp=100)
    bots = [human]
    actions = {"H": ("rest",)}

    observe_round(pt, ["H"], [], bots, storm_border=0, grid_size=10, actions=actions)

    assert pt.get_raw_counts("H", "after_damage") == {}
    assert pt.get_raw_counts("H", "at_range_1") == {}
    assert pt.get_raw_counts("H", "below_30_hp") == {}


def test_observe_round_action_tuple_normalized_to_first_element():
    """Action tuples like ('attack', 'north') should record 'attack'."""
    pt = PatternTable()
    human = _make_bot("H", x=3, y=3, hp=20)
    bots = [human]
    actions = {"H": ("attack", "north")}

    observe_round(pt, ["H"], [], bots, storm_border=0, grid_size=10, actions=actions)

    assert pt.get_raw_counts("H", "below_30_hp") == {"attack": 1}


def test_observe_round_skips_missing_action():
    """Human with no action in dict => skipped."""
    pt = PatternTable()
    human = _make_bot("H", x=3, y=3, hp=20)
    bots = [human]
    actions = {}  # no action for H

    observe_round(pt, ["H"], [], bots, storm_border=0, grid_size=10, actions=actions)

    assert pt.get_raw_counts("H", "below_30_hp") == {}
