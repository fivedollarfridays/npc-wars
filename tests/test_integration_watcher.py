"""Integration tests for The Cringe pipeline.

Validates that all Cringe subsystems (spawn, memory, brain, observer,
stats, spectacle) work together end-to-end without import errors,
type mismatches, or data-flow breakages.
"""

from __future__ import annotations

import random

from engine.combat import Bot
from engine.spectacle import SpectacleEngine
from engine.watcher import WATCHER_ACTIONS
from engine.watcher_brain import (
    COUNTER_MAP,
    HumanPerformance,
    SyncTracker,
    get_accuracy_cap,
    select_counter_action,
    select_target,
)
from engine.watcher_memory import PatternTable, load_memory, save_memory
from engine.watcher_spawn import (
    build_spawn_event,
    check_watcher_spawn,
    find_spawn_position,
)
from engine.watcher_spectacle import (
    emit_watcher_kill_event,
    emit_watcher_spawn_event,
)
from engine.watcher_stats import WatcherStats, load_stats, save_stats


def _make_bot(emoji: str, x: int, y: int, *, human: bool = False) -> Bot:
    """Create a test bot with optional human_adapter sentinel."""
    bot = Bot(
        name=f"bot-{emoji}",
        emoji=emoji,
        bio="test",
        author="test",
        decide_func=lambda s: ("rest",),
        x=x,
        y=y,
    )
    if human:
        bot.human_adapter = object()  # type: ignore[assignment]
    return bot


# -- 1. Spawn Test -----------------------------------------------------------


def test_spawn_too_early_returns_false() -> None:
    """Cringe should not spawn when human hasn't met thresholds."""
    human = _make_bot("H", 5, 5, human=True)
    bots = [human, _make_bot("A", 1, 1), _make_bot("B", 8, 8), _make_bot("C", 3, 7)]

    # Round 3 with default stats -- too early
    assert check_watcher_spawn(bots, round_num=3, watcher_present=False) is False


def test_spawn_conditions_met() -> None:
    """Cringe should spawn when human survived 5+ rounds with >50% HP."""
    human = _make_bot("H", 5, 5, human=True)
    human.rounds_survived = 5
    human.hp = 60  # >50% of MAX_HP=100
    bots = [human, _make_bot("A", 1, 1), _make_bot("B", 8, 8), _make_bot("C", 3, 7)]

    assert check_watcher_spawn(bots, round_num=5, watcher_present=False) is True


def test_spawn_position_far_from_humans() -> None:
    """Spawn position should be 3+ Manhattan distance from humans."""
    rng = random.Random(42)
    human_positions = [(5, 5)]
    pos = find_spawn_position(
        grid_size=20,
        storm_border=0,
        occupied=set(),
        human_positions=human_positions,
        rng=rng,
    )
    dist = abs(pos[0] - 5) + abs(pos[1] - 5)
    assert dist >= 3


def test_build_spawn_event_structure() -> None:
    """build_spawn_event returns correct event dict."""
    event = build_spawn_event(7, 9)
    assert event == {"type": "watcher_spawn", "x": 7, "y": 9}


# -- 2. Pattern Recording -> Prediction Pipeline -----------------------------


def test_pattern_record_and_predict() -> None:
    """Recording actions yields correct probability distribution."""
    pt = PatternTable()
    for _ in range(5):
        pt.record("player1", "after_damage", "attack")
    for _ in range(2):
        pt.record("player1", "after_damage", "defend")

    probs = pt.predict("player1", "after_damage")
    assert abs(probs["attack"] - 5 / 7) < 0.01
    assert abs(probs["defend"] - 2 / 7) < 0.01


def test_pattern_to_counter_action() -> None:
    """Predicted top action feeds into counter selection correctly."""
    pt = PatternTable()
    for _ in range(5):
        pt.record("player1", "after_damage", "attack")
    for _ in range(2):
        pt.record("player1", "after_damage", "defend")

    # Best prediction is "attack", counter is "defend"
    assert COUNTER_MAP["attack"] == "defend"

    result = select_counter_action(
        pattern_table=pt,
        target_id="player1",
        watcher_x=0,
        watcher_y=0,
        target_x=5,
        target_y=5,
        contexts=["after_damage"],
        all_actions=set(WATCHER_ACTIONS),
    )
    # Counter for "attack" is "defend", which is non-directional
    assert result[0] == "defend"


# -- 3. Sync Calculation -----------------------------------------------------


def test_sync_tracker_accuracy() -> None:
    """SyncTracker correctly computes accuracy percentage."""
    tracker = SyncTracker()
    for i in range(10):
        if i < 7:
            tracker.record_prediction("p1", "attack", "attack")  # correct
        else:
            tracker.record_prediction("p1", "attack", "defend")  # wrong

    assert tracker.get_sync("p1") == 70.0


# -- 4. Memory Persistence Roundtrip -----------------------------------------


def test_memory_save_load_roundtrip(tmp_path: object) -> None:
    """Saving and loading preserves PatternTable data."""
    from pathlib import Path

    path = str(Path(str(tmp_path)) / "watcher_mem.json")

    pt = PatternTable()
    pt.record("alice", "after_damage", "attack")
    pt.record("alice", "after_damage", "attack")
    pt.record("alice", "below_30_hp", "rest")

    save_memory(pt, path)
    loaded = load_memory(path)

    assert loaded.get_raw_counts("alice", "after_damage") == pt.get_raw_counts(
        "alice", "after_damage"
    )
    assert loaded.get_raw_counts("alice", "below_30_hp") == pt.get_raw_counts(
        "alice", "below_30_hp"
    )


# -- 5. Rubber-Banding -------------------------------------------------------


def test_rubber_band_losing_player() -> None:
    """Losing player gets lower accuracy cap (easier opponent)."""
    perf = HumanPerformance(hp_ratio=0.2, kills=0, rounds_survived=10)
    assert get_accuracy_cap(perf) == 0.60


def test_rubber_band_dominating_player() -> None:
    """Dominating player gets higher accuracy cap (harder opponent)."""
    perf = HumanPerformance(hp_ratio=0.8, kills=4, rounds_survived=20)
    assert get_accuracy_cap(perf) == 0.95


# -- 6. Target Rotation ------------------------------------------------------


def test_target_rotation_highest_sync() -> None:
    """select_target picks the player with highest sync."""
    tracker = SyncTracker()
    # Player A: 80% sync (8 correct, 2 wrong)
    for i in range(10):
        tracker.record_prediction("A", "x", "x" if i < 8 else "y")
    # Player B: 40% sync (4 correct, 6 wrong)
    for i in range(10):
        tracker.record_prediction("B", "x", "x" if i < 4 else "y")

    assert select_target(tracker, ["A", "B"]) == "A"


def test_target_rotation_switches_after_drop() -> None:
    """Target switches when sync drops below alternative."""
    tracker = SyncTracker()
    # Player A: 80% sync
    for i in range(10):
        tracker.record_prediction("A", "x", "x" if i < 8 else "y")
    # Player B: 40% sync
    for i in range(10):
        tracker.record_prediction("B", "x", "x" if i < 4 else "y")

    assert select_target(tracker, ["A", "B"]) == "A"

    # Record bad predictions for A until sync drops below B's 40%
    # Window is last 10, so 10 wrong predictions make A = 0%
    for _ in range(10):
        tracker.record_prediction("A", "x", "y")

    assert tracker.get_sync("A") == 0.0
    assert select_target(tracker, ["A", "B"]) == "B"


# -- 7. Spectacle Events -----------------------------------------------------


def test_spectacle_watcher_spawn_trigger() -> None:
    """SpectacleEngine detects watcher_spawn trigger from event."""
    engine = SpectacleEngine()
    spawn_event = emit_watcher_spawn_event(x=5, y=3, sync=15.0)
    result = engine.score_round([spawn_event], [])
    assert "watcher_spawn" in result.triggers


def test_spectacle_watcher_kill_trigger() -> None:
    """SpectacleEngine detects watcher_kill trigger from event."""
    engine = SpectacleEngine()
    kill_event = emit_watcher_kill_event(victim="duck", sync=73.0)
    result = engine.score_round([kill_event], [])
    assert "watcher_kill" in result.triggers


# -- 8. Stats Tracking -------------------------------------------------------


def test_stats_record_and_verify() -> None:
    """WatcherStats records kills, deaths, matches correctly."""
    stats = WatcherStats()
    stats.record_kill("human")
    stats.record_kill("bot")
    stats.record_kill("bot")
    stats.record_death()
    stats.record_match(won=True)
    stats.record_match(won=False)
    stats.record_encounter("player1", won=True)

    assert stats.kills == 3
    assert stats.human_kills == 1
    assert stats.bot_kills == 2
    assert stats.deaths == 1
    assert stats.matches == 2
    assert stats.wins == 1
    assert stats.current_streak == 0  # lost last match
    assert stats.encounters["player1"] == {"count": 1, "wins": 1}


def test_stats_save_load_roundtrip(tmp_path: object) -> None:
    """Save/load preserves WatcherStats data."""
    from pathlib import Path

    path = str(Path(str(tmp_path)) / "watcher_stats.json")

    stats = WatcherStats()
    stats.record_kill("human")
    stats.record_kill("bot")
    stats.record_death()
    stats.record_match(won=True)
    stats.record_encounter("p1", won=True)

    save_stats(stats, path)
    loaded = load_stats(path)

    assert loaded.kills == stats.kills
    assert loaded.human_kills == stats.human_kills
    assert loaded.bot_kills == stats.bot_kills
    assert loaded.deaths == stats.deaths
    assert loaded.matches == stats.matches
    assert loaded.wins == stats.wins
    assert loaded.encounters == stats.encounters


# -- 9. Full Pipeline Test ---------------------------------------------------


def test_full_pipeline_5_rounds() -> None:
    """End-to-end: PatternTable + SyncTracker + SpectacleEngine over 5 rounds."""
    pt = PatternTable()
    sync = SyncTracker()
    spectacle = SpectacleEngine()

    human_id = "H"
    context = "after_damage"

    # Round 1-2: Record human actions (observer-style)
    for _ in range(2):
        pt.record(human_id, context, "attack")

    # Verify data accumulated
    counts = pt.get_raw_counts(human_id, context)
    assert counts["attack"] == 2

    # Round 3: Use select_counter_action with recorded data
    counter = select_counter_action(
        pattern_table=pt,
        target_id=human_id,
        watcher_x=0,
        watcher_y=0,
        target_x=3,
        target_y=3,
        contexts=[context],
        all_actions=set(WATCHER_ACTIONS),
    )
    assert isinstance(counter, tuple)
    assert len(counter) >= 1
    assert counter[0] in WATCHER_ACTIONS

    # Round 4: Record prediction result, check sync updated
    predicted = "attack"  # best prediction from pattern table
    actual = "attack"  # human did attack again
    sync.record_prediction(human_id, predicted, actual)
    assert sync.get_sync(human_id) == 100.0

    # Record another where prediction is wrong
    sync.record_prediction(human_id, "attack", "defend")
    assert sync.get_sync(human_id) == 50.0

    # Round 5: Generate spectacle event
    spawn_event = emit_watcher_spawn_event(x=5, y=3, sync=sync.get_sync(human_id))
    result = spectacle.score_round([spawn_event], [])
    assert "watcher_spawn" in result.triggers
    assert result.drama_score > 0
