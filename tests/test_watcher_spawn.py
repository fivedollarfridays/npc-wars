"""Tests for engine.watcher_spawn — Watcher spawn conditions & mid-match entry."""

from __future__ import annotations

import random


class FakeBot:
    """Minimal Bot stand-in for spawn tests."""

    def __init__(
        self,
        *,
        hp: int = 100,
        kills: int = 0,
        rounds_survived: int = 0,
        alive: bool = True,
        human_adapter: object | None = None,
        x: int = 0,
        y: int = 0,
        emoji: str = "\U0001f986",
        is_watcher: bool = False,
    ) -> None:
        self.hp = hp
        self.kills = kills
        self.rounds_survived = rounds_survived
        self.alive = alive
        self.human_adapter = human_adapter
        self.x = x
        self.y = y
        self.emoji = emoji
        self.is_watcher = is_watcher


# ---------------------------------------------------------------------------
# check_watcher_spawn
# ---------------------------------------------------------------------------

class TestCheckWatcherSpawn:
    """Tests for check_watcher_spawn()."""

    def test_returns_false_pure_bot_match(self) -> None:
        """No human bots present => False."""
        from engine.watcher_spawn import check_watcher_spawn

        bots = [FakeBot(), FakeBot(), FakeBot()]
        assert check_watcher_spawn(bots, round_num=10, watcher_present=False) is False

    def test_returns_false_if_watcher_already_present(self) -> None:
        """Watcher already in the match => False."""
        from engine.watcher_spawn import check_watcher_spawn

        human = FakeBot(human_adapter=object(), rounds_survived=10, hp=80, kills=2)
        bots = [human, FakeBot()]
        assert check_watcher_spawn(bots, round_num=10, watcher_present=True) is False

    def test_returns_true_human_survived_5_rounds_above_50_hp(self) -> None:
        """Human survived 5+ rounds with >50% HP => True."""
        from engine.watcher_spawn import check_watcher_spawn

        human = FakeBot(human_adapter=object(), rounds_survived=5, hp=51)
        bots = [human, FakeBot()]
        assert check_watcher_spawn(bots, round_num=6, watcher_present=False) is True

    def test_returns_false_human_survived_5_rounds_low_hp_no_kills(self) -> None:
        """Human survived 5+ rounds but HP <= 50 and no kills => False."""
        from engine.watcher_spawn import check_watcher_spawn

        human = FakeBot(human_adapter=object(), rounds_survived=5, hp=50, kills=0)
        bots = [human, FakeBot()]
        assert check_watcher_spawn(bots, round_num=6, watcher_present=False) is False

    def test_returns_true_human_has_kills(self) -> None:
        """Human has kills > 0 => True (regardless of rounds/HP)."""
        from engine.watcher_spawn import check_watcher_spawn

        human = FakeBot(human_adapter=object(), rounds_survived=1, hp=30, kills=1)
        bots = [human, FakeBot()]
        assert check_watcher_spawn(bots, round_num=2, watcher_present=False) is True

    def test_returns_false_dead_human_with_kills(self) -> None:
        """Dead human should not trigger spawn."""
        from engine.watcher_spawn import check_watcher_spawn

        human = FakeBot(human_adapter=object(), alive=False, kills=3)
        bots = [human, FakeBot()]
        assert check_watcher_spawn(bots, round_num=5, watcher_present=False) is False


# ---------------------------------------------------------------------------
# find_spawn_position
# ---------------------------------------------------------------------------

class TestFindSpawnPosition:
    """Tests for find_spawn_position()."""

    def test_position_3_plus_manhattan_from_humans(self) -> None:
        """Spawn position must be >= 3 Manhattan distance from all humans."""
        from engine.watcher_spawn import find_spawn_position

        rng = random.Random(42)
        human_positions = [(5, 5)]
        pos = find_spawn_position(
            grid_size=20,
            storm_border=0,
            occupied=set(),
            human_positions=human_positions,
            rng=rng,
        )
        x, y = pos
        for hx, hy in human_positions:
            assert abs(x - hx) + abs(y - hy) >= 3

    def test_position_inside_grid_not_in_storm(self) -> None:
        """Spawn position must be valid and not in storm."""
        from engine.watcher_spawn import find_spawn_position
        from engine.grid import is_valid_position, is_in_storm

        rng = random.Random(99)
        pos = find_spawn_position(
            grid_size=20,
            storm_border=3,
            occupied=set(),
            human_positions=[(10, 10)],
            rng=rng,
        )
        x, y = pos
        assert is_valid_position(x, y, 20)
        assert not is_in_storm(x, y, 20, 3)

    def test_position_not_occupied(self) -> None:
        """Spawn position must not be in the occupied set."""
        from engine.watcher_spawn import find_spawn_position

        rng = random.Random(7)
        # Fill most of the grid as occupied, leaving few spots open
        occupied = {(x, y) for x in range(20) for y in range(20)}
        # Leave a few positions open far from human
        open_positions = [(15, 15), (16, 16), (17, 17)]
        for p in open_positions:
            occupied.discard(p)

        pos = find_spawn_position(
            grid_size=20,
            storm_border=0,
            occupied=occupied,
            human_positions=[(0, 0)],
            rng=rng,
        )
        assert pos not in occupied

    def test_fallback_when_distance_impossible(self) -> None:
        """Falls back to any valid unoccupied position when 3+ distance impossible."""
        from engine.watcher_spawn import find_spawn_position

        # Tiny 4x4 grid, human at center — hard to be 3+ away
        rng = random.Random(123)
        pos = find_spawn_position(
            grid_size=4,
            storm_border=0,
            occupied=set(),
            human_positions=[(2, 2)],
            rng=rng,
        )
        x, y = pos
        assert 0 <= x < 4 and 0 <= y < 4


# ---------------------------------------------------------------------------
# build_spawn_event
# ---------------------------------------------------------------------------

class TestBuildSpawnEvent:
    """Tests for build_spawn_event()."""

    def test_returns_correct_event_dict(self) -> None:
        """Event dict has type, x, y keys."""
        from engine.watcher_spawn import build_spawn_event

        event = build_spawn_event(7, 12)
        assert event == {"type": "watcher_spawn", "x": 7, "y": 12}
