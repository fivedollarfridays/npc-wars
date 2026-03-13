"""Tests for update_streak() in data/player_profiles.py."""

from data.player_profiles import PlayerProfile, update_streak


class TestWinIncrementsStreak:
    """Wins increment current_streak."""

    def test_first_win_increments_from_zero(self) -> None:
        p = PlayerProfile(player_id="p1", bot_name="Bot", emoji="X")
        update_streak(p, is_winner=True)
        assert p.current_streak == 1

    def test_consecutive_wins_increment(self) -> None:
        p = PlayerProfile(
            player_id="p1", bot_name="Bot", emoji="X", current_streak=1
        )
        update_streak(p, is_winner=True)
        assert p.current_streak == 2
        update_streak(p, is_winner=True)
        assert p.current_streak == 3


class TestLossResetsStreak:
    """Losses reset current_streak to 0."""

    def test_loss_resets_current_streak(self) -> None:
        p = PlayerProfile(
            player_id="p1", bot_name="Bot", emoji="X", current_streak=5
        )
        update_streak(p, is_winner=False)
        assert p.current_streak == 0


class TestBestStreakTracking:
    """best_streak tracks the highest current_streak ever reached."""

    def test_best_streak_updated_on_new_record(self) -> None:
        p = PlayerProfile(
            player_id="p1", bot_name="Bot", emoji="X",
            current_streak=2, best_streak=2,
        )
        update_streak(p, is_winner=True)
        assert p.best_streak == 3

    def test_loss_does_not_reset_best_streak(self) -> None:
        p = PlayerProfile(
            player_id="p1", bot_name="Bot", emoji="X",
            current_streak=3, best_streak=5,
        )
        update_streak(p, is_winner=False)
        assert p.best_streak == 5

    def test_best_streak_unchanged_when_not_exceeded(self) -> None:
        p = PlayerProfile(
            player_id="p1", bot_name="Bot", emoji="X",
            current_streak=1, best_streak=10,
        )
        update_streak(p, is_winner=True)
        assert p.current_streak == 2
        assert p.best_streak == 10

    def test_first_win_sets_both_streaks(self) -> None:
        p = PlayerProfile(player_id="p1", bot_name="Bot", emoji="X")
        assert p.current_streak == 0
        assert p.best_streak == 0
        update_streak(p, is_winner=True)
        assert p.current_streak == 1
        assert p.best_streak == 1
