"""Tests for engine/grid.py — bounds, directions, grid size."""

import pytest

from engine.grid import (
    DIRECTIONS,
    apply_direction,
    calculate_grid_size,
    get_storm_border,
    is_valid_position,
)


# --- get_storm_border clamp (safe zone never below 2x2) ---


class TestStormBorderClamp:
    def test_safe_zone_never_below_2x2_across_grid_sizes(self):
        """Safe-zone side = grid_size - 2*border must stay >= 2 at all rounds."""
        for grid_size in (10, 15, 20, 25, 30):
            for round_num in range(0, 121):
                border = get_storm_border(round_num, grid_size)
                safe_side = grid_size - 2 * border
                assert safe_side >= 2, (
                    f"grid={grid_size} round={round_num} border={border} "
                    f"safe_side={safe_side} < 2"
                )

    def test_clamp_bound_matches_formula(self):
        """Late-game border is clamped to (grid_size - 2) // 2."""
        for grid_size in (10, 12, 15, 20, 25, 30):
            max_border = (grid_size - 2) // 2
            assert get_storm_border(200, grid_size) == max_border

    def test_returns_int(self):
        assert isinstance(get_storm_border(100, 12), int)

    def test_backward_compat_no_grid_size_unclamped(self):
        """Without grid_size, value is unclamped (legacy behavior)."""
        assert get_storm_border(49) == 14


# --- is_valid_position ---


class TestIsValidPosition:
    def test_origin_valid(self):
        assert is_valid_position(0, 0, 10) is True

    def test_max_corner_valid(self):
        assert is_valid_position(9, 9, 10) is True

    def test_center_valid(self):
        assert is_valid_position(5, 5, 10) is True

    def test_negative_x_invalid(self):
        assert is_valid_position(-1, 0, 10) is False

    def test_negative_y_invalid(self):
        assert is_valid_position(0, -1, 10) is False

    def test_x_at_grid_size_invalid(self):
        assert is_valid_position(10, 0, 10) is False

    def test_y_at_grid_size_invalid(self):
        assert is_valid_position(0, 10, 10) is False

    def test_both_out_of_bounds(self):
        assert is_valid_position(-1, 10, 10) is False

    def test_grid_size_1(self):
        assert is_valid_position(0, 0, 1) is True
        assert is_valid_position(1, 0, 1) is False


# --- DIRECTIONS ---


class TestDirections:
    def test_north_decreases_y(self):
        assert DIRECTIONS["north"] == (0, -1)

    def test_south_increases_y(self):
        assert DIRECTIONS["south"] == (0, 1)

    def test_east_increases_x(self):
        assert DIRECTIONS["east"] == (1, 0)

    def test_west_decreases_x(self):
        assert DIRECTIONS["west"] == (-1, 0)

    def test_exactly_four_directions(self):
        assert set(DIRECTIONS.keys()) == {"north", "south", "east", "west"}


# --- apply_direction ---


class TestApplyDirection:
    def test_move_north(self):
        assert apply_direction(5, 5, "north") == (5, 4)

    def test_move_south(self):
        assert apply_direction(5, 5, "south") == (5, 6)

    def test_move_east(self):
        assert apply_direction(5, 5, "east") == (6, 5)

    def test_move_west(self):
        assert apply_direction(5, 5, "west") == (4, 5)

    def test_invalid_direction_raises(self):
        with pytest.raises(KeyError):
            apply_direction(5, 5, "up")


# --- calculate_grid_size ---


class TestCalculateGridSize:
    def test_minimum_grid_size_is_10(self):
        assert calculate_grid_size(1) == 10

    def test_small_player_count(self):
        assert calculate_grid_size(4) == 10  # sqrt(4)*5 = 10

    def test_larger_player_count(self):
        assert calculate_grid_size(9) == 15  # sqrt(9)*5 = 15

    def test_16_players(self):
        assert calculate_grid_size(16) == 20  # sqrt(16)*5 = 20
