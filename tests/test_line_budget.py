"""Tests for line budget tracking in data/player_profiles.py."""

from data.player_profiles import (
    BUDGET_BASE,
    BUDGET_CAP,
    BUDGET_PER_WIN,
    BUDGET_WATCHER_BONUS,
    PlayerProfile,
    calculate_line_budget,
    update_after_match,
)


class TestLineBudgetConstants:
    """Budget constants have expected values."""

    def test_budget_base(self) -> None:
        assert BUDGET_BASE == 50

    def test_budget_cap(self) -> None:
        assert BUDGET_CAP == 200

    def test_new_profile_has_base_budget(self) -> None:
        p = PlayerProfile(player_id="p1", bot_name="B", emoji="X")
        assert p.line_budget == BUDGET_BASE


class TestCalculateLineBudget:
    """calculate_line_budget applies wins, streaks, and Watcher bonuses."""

    def test_single_win(self) -> None:
        p = PlayerProfile(player_id="p1", bot_name="B", emoji="X", wins=1)
        result = calculate_line_budget(p)
        assert result == BUDGET_BASE + BUDGET_PER_WIN  # 50 + 10 = 60

    def test_streak_3_bonus(self) -> None:
        p = PlayerProfile(
            player_id="p1", bot_name="B", emoji="X", wins=1, best_streak=3
        )
        result = calculate_line_budget(p)
        # 50 + 10 + 15 = 75
        assert result == 75

    def test_streak_5_bonus(self) -> None:
        p = PlayerProfile(
            player_id="p1", bot_name="B", emoji="X", wins=1, best_streak=5
        )
        result = calculate_line_budget(p)
        # 50 + 10 + 25 = 85
        assert result == 85

    def test_streak_10_bonus(self) -> None:
        p = PlayerProfile(
            player_id="p1", bot_name="B", emoji="X", wins=1, best_streak=10
        )
        result = calculate_line_budget(p)
        # 50 + 10 + 50 = 110
        assert result == 110

    def test_budget_capped_at_200(self) -> None:
        p = PlayerProfile(
            player_id="p1", bot_name="B", emoji="X", wins=100, best_streak=10
        )
        result = calculate_line_budget(p)
        assert result == BUDGET_CAP  # 200

    def test_watcher_win_bonus(self) -> None:
        p = PlayerProfile(
            player_id="p1", bot_name="B", emoji="X", wins=0, watcher_wins=1
        )
        result = calculate_line_budget(p)
        # 50 + 0 + 0 + 20 = 70
        assert result == BUDGET_BASE + BUDGET_WATCHER_BONUS

    def test_zero_wins_zero_streak(self) -> None:
        p = PlayerProfile(player_id="p1", bot_name="B", emoji="X")
        result = calculate_line_budget(p)
        assert result == BUDGET_BASE


class TestUpdateAfterMatch:
    """update_after_match mutates profile correctly."""

    def test_winner_increments_wins(self) -> None:
        p = PlayerProfile(player_id="p1", bot_name="B", emoji="X", wins=2)
        update_after_match(p, is_winner=True)
        assert p.wins == 3

    def test_winner_recalculates_budget(self) -> None:
        p = PlayerProfile(player_id="p1", bot_name="B", emoji="X", wins=0)
        update_after_match(p, is_winner=True)
        # After: wins=1, budget = 50 + 10 = 60
        assert p.line_budget == 60

    def test_loser_does_not_increment_wins(self) -> None:
        p = PlayerProfile(player_id="p1", bot_name="B", emoji="X", wins=5)
        old_budget = p.line_budget
        update_after_match(p, is_winner=False)
        assert p.wins == 5
        assert p.line_budget == old_budget

    def test_beat_watcher_increments_watcher_wins(self) -> None:
        p = PlayerProfile(player_id="p1", bot_name="B", emoji="X", watcher_wins=0)
        update_after_match(p, is_winner=True, beat_watcher=True)
        assert p.watcher_wins == 1

    def test_beat_watcher_false_no_increment(self) -> None:
        p = PlayerProfile(player_id="p1", bot_name="B", emoji="X", watcher_wins=0)
        update_after_match(p, is_winner=True, beat_watcher=False)
        assert p.watcher_wins == 0
