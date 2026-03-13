"""Tests for engine/grid.py — storm border, is_in_storm, spawn positions."""

import random

from engine.grid import (
    get_storm_border,
    is_in_storm,
    spawn_positions,
)


# --- get_storm_border ---


class TestGetStormBorder:
    def test_no_storm_round_1(self):
        assert get_storm_border(1) == 0

    def test_no_storm_round_20(self):
        assert get_storm_border(20) == 0

    def test_storm_starts_round_21(self):
        # (21-20)//5 = 0 — first 5-round block hasn't completed
        assert get_storm_border(21) == 0

    def test_storm_round_25(self):
        # (25-20)//5 = 1
        assert get_storm_border(25) == 1

    def test_storm_round_30(self):
        # (30-20)//5 = 2
        assert get_storm_border(30) == 2

    def test_storm_round_40(self):
        # (40-20)//5 = 4
        assert get_storm_border(40) == 4

    def test_endgame_round_41(self):
        # closing_border=4, (41-40)//2 = 0 → 4
        assert get_storm_border(41) == 4

    def test_endgame_round_42(self):
        # closing_border=4, (42-40)//2 = 1 → 5
        assert get_storm_border(42) == 5

    def test_endgame_round_50(self):
        # closing_border=4, (50-40)//2 = 5 → 9
        assert get_storm_border(50) == 9

    def test_endgame_round_60(self):
        # closing_border=4, (60-40)//2 = 10 → 14
        assert get_storm_border(60) == 14

    def test_monotonically_increasing(self):
        borders = [get_storm_border(r) for r in range(1, 100)]
        for i in range(1, len(borders)):
            assert borders[i] >= borders[i - 1]


# --- is_in_storm ---


class TestIsInStorm:
    def test_no_storm_when_border_0(self):
        assert is_in_storm(0, 0, 10, 0) is False

    def test_corner_in_storm_border_1(self):
        assert is_in_storm(0, 0, 10, 1) is True

    def test_edge_in_storm_border_1(self):
        assert is_in_storm(0, 5, 10, 1) is True

    def test_just_inside_safe_zone(self):
        assert is_in_storm(1, 1, 10, 1) is False

    def test_opposite_edge_in_storm(self):
        assert is_in_storm(9, 9, 10, 1) is True

    def test_just_inside_safe_on_far_side(self):
        assert is_in_storm(8, 8, 10, 1) is False

    def test_border_2_deeper_safe(self):
        # border=2: safe zone is x in [2,7], y in [2,7] for grid_size=10
        assert is_in_storm(1, 5, 10, 2) is True
        assert is_in_storm(2, 5, 10, 2) is False
        assert is_in_storm(8, 5, 10, 2) is True
        assert is_in_storm(7, 5, 10, 2) is False

    def test_negative_border_no_storm(self):
        assert is_in_storm(0, 0, 10, -1) is False

    def test_center_always_safe(self):
        assert is_in_storm(5, 5, 10, 1) is False
        assert is_in_storm(5, 5, 10, 3) is False


# --- spawn_positions ---


class TestSpawnPositions:
    def test_returns_correct_count(self):
        rng = random.Random(42)
        positions = spawn_positions(5, 15, rng)
        assert len(positions) == 5

    def test_all_within_edge_buffer(self):
        rng = random.Random(42)
        positions = spawn_positions(5, 15, rng)
        for x, y in positions:
            assert 2 <= x <= 12  # edge_buffer=2, grid_size-1-edge_buffer=12
            assert 2 <= y <= 12

    def test_minimum_spacing_between_bots(self):
        rng = random.Random(42)
        positions = spawn_positions(5, 15, rng)
        for i, (x1, y1) in enumerate(positions):
            for j, (x2, y2) in enumerate(positions):
                if i != j:
                    manhattan = abs(x1 - x2) + abs(y1 - y2)
                    assert manhattan >= 3, f"Positions {i} and {j} too close: {manhattan}"

    def test_no_duplicate_positions(self):
        rng = random.Random(42)
        positions = spawn_positions(5, 15, rng)
        assert len(set(positions)) == len(positions)

    def test_deterministic_with_seed(self):
        pos1 = spawn_positions(5, 15, random.Random(42))
        pos2 = spawn_positions(5, 15, random.Random(42))
        assert pos1 == pos2

    def test_fallback_on_tight_grid(self):
        """With many players on small grid, fallback relaxes spacing."""
        rng = random.Random(42)
        # 10 players on grid_size=10 — tight fit
        positions = spawn_positions(10, 10, rng)
        assert len(positions) == 10
        # All within bounds
        for x, y in positions:
            assert 2 <= x <= 7
            assert 2 <= y <= 7
