"""Tests for the WatcherController — orchestrates The Cringe lifecycle."""

from __future__ import annotations

import random

from engine.combat import Bot
from engine.watcher import WATCHER_EMOJI


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


# -- Cycle 1: Initialization -------------------------------------------------

def test_controller_init_empty_memory(tmp_path):
    """Controller starts with empty pattern table when no save file exists."""
    from engine.watcher_controller import WatcherController

    ctrl = WatcherController(rng=random.Random(42), memory_path=str(tmp_path / "mem.json"),
                             stats_path=str(tmp_path / "stats.json"))
    assert ctrl.watcher_bot is None
    assert ctrl.pattern_table is not None
    assert ctrl.sync_tracker is not None


def test_controller_loads_existing_memory(tmp_path):
    """Controller loads cross-session memory if save file exists."""
    from engine.watcher_controller import WatcherController
    from engine.watcher_memory import PatternTable, save_memory

    pt = PatternTable()
    pt.record("player1", "at_range_1", "attack")
    save_memory(pt, str(tmp_path / "mem.json"))

    ctrl = WatcherController(rng=random.Random(42), memory_path=str(tmp_path / "mem.json"),
                             stats_path=str(tmp_path / "stats.json"))
    # Cross-session decay applied, so counts should be reduced but non-zero
    raw = ctrl.pattern_table.get_raw_counts("player1", "at_range_1")
    assert raw.get("attack", 0) > 0
    assert raw["attack"] < 1.0  # decayed from 1


# -- Cycle 2: Spawn ----------------------------------------------------------

def test_try_spawn_returns_empty_when_no_humans(tmp_path):
    """try_spawn returns empty list when no human bots are present."""
    from engine.watcher_controller import WatcherController

    ctrl = WatcherController(rng=random.Random(42), memory_path=str(tmp_path / "mem.json"),
                             stats_path=str(tmp_path / "stats.json"))
    bots = [_make_bot("A", 3, 3), _make_bot("B", 5, 5)]
    events = ctrl.try_spawn(bots, round_num=10, grid_size=10, storm_border=0)
    assert events == []
    assert ctrl.watcher_bot is None


def test_try_spawn_returns_events_when_conditions_met(tmp_path):
    """try_spawn creates WatcherBot and returns events when conditions met."""
    from engine.watcher_controller import WatcherController

    ctrl = WatcherController(rng=random.Random(42), memory_path=str(tmp_path / "mem.json"),
                             stats_path=str(tmp_path / "stats.json"))
    human = _make_bot("H", 3, 3, human=True)
    human.kills = 1  # trigger spawn condition
    bots = [human, _make_bot("B", 5, 5)]
    events = ctrl.try_spawn(bots, round_num=10, grid_size=10, storm_border=0)
    assert len(events) >= 1
    assert ctrl.watcher_bot is not None
    assert ctrl.watcher_bot.emoji == WATCHER_EMOJI
    # Watcher should be added to bots list
    assert any(b.emoji == WATCHER_EMOJI for b in bots)


def test_try_spawn_no_double_spawn(tmp_path):
    """try_spawn returns empty if watcher already present."""
    from engine.watcher_controller import WatcherController

    ctrl = WatcherController(rng=random.Random(42), memory_path=str(tmp_path / "mem.json"),
                             stats_path=str(tmp_path / "stats.json"))
    human = _make_bot("H", 3, 3, human=True)
    human.kills = 1
    bots = [human, _make_bot("B", 5, 5)]
    ctrl.try_spawn(bots, round_num=10, grid_size=10, storm_border=0)
    assert ctrl.watcher_bot is not None
    # Second call should be no-op
    events2 = ctrl.try_spawn(bots, round_num=11, grid_size=10, storm_border=0)
    assert events2 == []


# -- Cycle 3: Get watcher action ----------------------------------------------

def test_get_watcher_action_returns_none_when_not_spawned(tmp_path):
    """get_watcher_action returns None if watcher hasn't spawned."""
    from engine.watcher_controller import WatcherController

    ctrl = WatcherController(rng=random.Random(42), memory_path=str(tmp_path / "mem.json"),
                             stats_path=str(tmp_path / "stats.json"))
    bots = [_make_bot("H", 3, 3, human=True)]
    result = ctrl.get_watcher_action(bots, round_num=1, grid_size=10, storm_border=0)
    assert result is None


def test_get_watcher_action_returns_valid_tuple(tmp_path):
    """get_watcher_action returns a valid action tuple when watcher is alive."""
    from engine.watcher_controller import WatcherController

    ctrl = WatcherController(rng=random.Random(42), memory_path=str(tmp_path / "mem.json"),
                             stats_path=str(tmp_path / "stats.json"))
    human = _make_bot("H", 3, 3, human=True)
    human.kills = 1
    bots = [human, _make_bot("B", 5, 5)]
    ctrl.try_spawn(bots, round_num=10, grid_size=10, storm_border=0)
    action = ctrl.get_watcher_action(bots, round_num=11, grid_size=10, storm_border=0)
    assert action is not None
    assert isinstance(action, tuple)
    assert len(action) >= 1
    assert action[0] in ("attack", "dash", "defend", "move", "ranged_attack", "rest", "taunt")


def test_get_watcher_action_rests_when_no_humans_alive(tmp_path):
    """get_watcher_action returns rest if all humans are dead."""
    from engine.watcher_controller import WatcherController

    ctrl = WatcherController(rng=random.Random(42), memory_path=str(tmp_path / "mem.json"),
                             stats_path=str(tmp_path / "stats.json"))
    human = _make_bot("H", 3, 3, human=True)
    human.kills = 1
    bots = [human, _make_bot("B", 5, 5)]
    ctrl.try_spawn(bots, round_num=10, grid_size=10, storm_border=0)
    # Kill the human
    human.alive = False
    action = ctrl.get_watcher_action(bots, round_num=11, grid_size=10, storm_border=0)
    assert action == ("rest",)


# -- Cycle 4: Observe ---------------------------------------------------------

def test_observe_records_to_pattern_table(tmp_path):
    """observe() records human actions into the pattern table."""
    from engine.watcher_controller import WatcherController

    ctrl = WatcherController(rng=random.Random(42), memory_path=str(tmp_path / "mem.json"),
                             stats_path=str(tmp_path / "stats.json"))
    human = _make_bot("H", 3, 3, human=True)
    bots = [human, _make_bot("B", 1, 1)]
    actions = {"H": ("attack", "north"), "B": ("rest",)}
    # Simulate a round event where H was hit (to trigger "after_damage" context)
    round_events = [{"type": "hit", "target": "H", "attacker": "B", "damage": 10}]
    ctrl.observe(["H"], round_events, bots, storm_border=0, grid_size=10, actions=actions)
    raw = ctrl.pattern_table.get_raw_counts("H", "after_damage")
    assert raw.get("attack", 0) > 0


# -- Cycle 5: Record kill & finalize ------------------------------------------

def test_record_kill_by_watcher(tmp_path):
    """record_kill tracks kills made by the watcher."""
    from engine.watcher_controller import WatcherController

    ctrl = WatcherController(rng=random.Random(42), memory_path=str(tmp_path / "mem.json"),
                             stats_path=str(tmp_path / "stats.json"))
    human = _make_bot("H", 3, 3, human=True)
    human.kills = 1
    bots = [human, _make_bot("B", 5, 5)]
    ctrl.try_spawn(bots, round_num=10, grid_size=10, storm_border=0)
    events = ctrl.record_kill(WATCHER_EMOJI, "H", ["H"])
    assert len(events) >= 1
    assert ctrl.stats.human_kills == 1


def test_record_watcher_death(tmp_path):
    """record_kill tracks deaths of the watcher."""
    from engine.watcher_controller import WatcherController

    ctrl = WatcherController(rng=random.Random(42), memory_path=str(tmp_path / "mem.json"),
                             stats_path=str(tmp_path / "stats.json"))
    human = _make_bot("H", 3, 3, human=True)
    human.kills = 1
    bots = [human, _make_bot("B", 5, 5)]
    ctrl.try_spawn(bots, round_num=10, grid_size=10, storm_border=0)
    ctrl.record_kill("H", WATCHER_EMOJI, ["H"])
    assert ctrl.stats.deaths == 1


def test_finalize_saves_memory_and_stats(tmp_path):
    """finalize() persists memory and stats to disk."""
    from engine.watcher_controller import WatcherController
    from engine.watcher_memory import load_memory
    from engine.watcher_stats import load_stats

    mem_path = str(tmp_path / "mem.json")
    stats_path = str(tmp_path / "stats.json")
    ctrl = WatcherController(rng=random.Random(42), memory_path=mem_path, stats_path=stats_path)

    # Record some data
    ctrl.pattern_table.record("H", "at_range_1", "attack")
    ctrl.finalize(won=True)

    # Verify files written
    loaded_pt = load_memory(mem_path)
    assert loaded_pt.get_raw_counts("H", "at_range_1").get("attack", 0) > 0
    loaded_stats = load_stats(stats_path)
    assert loaded_stats.matches == 1
    assert loaded_stats.wins == 1
