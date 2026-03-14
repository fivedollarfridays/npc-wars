"""Tests for The Cringe sync rating calculation."""

from __future__ import annotations

from engine.watcher_brain import SyncTracker


class TestSyncTrackerNewPlayer:
    """Cycle 1: New player starts at 0% sync."""

    def test_unknown_player_returns_zero(self) -> None:
        tracker = SyncTracker()
        assert tracker.get_sync("player_a") == 0.0

    def test_get_sync_returns_float(self) -> None:
        tracker = SyncTracker()
        result = tracker.get_sync("player_a")
        assert isinstance(result, float)


class TestSyncTrackerPredictions:
    """Cycle 2: Correct predictions increase sync, incorrect decrease it."""

    def test_correct_prediction_increases_sync(self) -> None:
        tracker = SyncTracker()
        tracker.record_prediction("p1", "attack", "attack")
        assert tracker.get_sync("p1") == 100.0

    def test_incorrect_prediction_gives_zero(self) -> None:
        tracker = SyncTracker()
        tracker.record_prediction("p1", "attack", "defend")
        assert tracker.get_sync("p1") == 0.0

    def test_mixed_predictions_give_percentage(self) -> None:
        tracker = SyncTracker()
        tracker.record_prediction("p1", "attack", "attack")  # correct
        tracker.record_prediction("p1", "attack", "defend")  # wrong
        assert tracker.get_sync("p1") == 50.0

    def test_three_of_four_correct(self) -> None:
        tracker = SyncTracker()
        tracker.record_prediction("p1", "attack", "attack")
        tracker.record_prediction("p1", "defend", "defend")
        tracker.record_prediction("p1", "move", "move")
        tracker.record_prediction("p1", "rest", "attack")
        assert tracker.get_sync("p1") == 75.0

    def test_breaking_pattern_drops_sync(self) -> None:
        tracker = SyncTracker()
        # Build up 100% sync
        for _ in range(5):
            tracker.record_prediction("p1", "attack", "attack")
        assert tracker.get_sync("p1") == 100.0
        # Player breaks pattern
        tracker.record_prediction("p1", "attack", "defend")
        # Now 5/6 correct
        expected = (5 / 6) * 100.0
        assert abs(tracker.get_sync("p1") - expected) < 0.01


class TestSyncTrackerBounds:
    """Cycle 3: Sync rating capped at 0% min, 100% max."""

    def test_sync_never_below_zero(self) -> None:
        tracker = SyncTracker()
        for _ in range(20):
            tracker.record_prediction("p1", "attack", "defend")
        assert tracker.get_sync("p1") == 0.0

    def test_sync_never_above_hundred(self) -> None:
        tracker = SyncTracker()
        for _ in range(20):
            tracker.record_prediction("p1", "attack", "attack")
        assert tracker.get_sync("p1") == 100.0


class TestSyncTrackerPerPlayer:
    """Cycle 4: Per-player isolation."""

    def test_player_a_does_not_affect_player_b(self) -> None:
        tracker = SyncTracker()
        tracker.record_prediction("a", "attack", "attack")
        tracker.record_prediction("b", "attack", "defend")
        assert tracker.get_sync("a") == 100.0
        assert tracker.get_sync("b") == 0.0

    def test_multiple_players_independent(self) -> None:
        tracker = SyncTracker()
        # Player A: 2/3 correct
        tracker.record_prediction("a", "attack", "attack")
        tracker.record_prediction("a", "defend", "defend")
        tracker.record_prediction("a", "move", "rest")
        # Player B: 1/2 correct
        tracker.record_prediction("b", "attack", "attack")
        tracker.record_prediction("b", "defend", "move")
        expected_a = (2 / 3) * 100.0
        expected_b = 50.0
        assert abs(tracker.get_sync("a") - expected_a) < 0.01
        assert tracker.get_sync("b") == expected_b


class TestSyncTrackerRollingWindow:
    """Cycle 5: Rolling window of last 10 predictions."""

    def test_window_limited_to_ten(self) -> None:
        tracker = SyncTracker()
        # 10 wrong predictions
        for _ in range(10):
            tracker.record_prediction("p1", "attack", "defend")
        assert tracker.get_sync("p1") == 0.0
        # Now 10 correct predictions push out the wrong ones
        for _ in range(10):
            tracker.record_prediction("p1", "attack", "attack")
        assert tracker.get_sync("p1") == 100.0

    def test_eleventh_prediction_drops_first(self) -> None:
        tracker = SyncTracker()
        # 10 correct
        for _ in range(10):
            tracker.record_prediction("p1", "attack", "attack")
        assert tracker.get_sync("p1") == 100.0
        # 11th is wrong: now 9/10 correct
        tracker.record_prediction("p1", "attack", "defend")
        assert tracker.get_sync("p1") == 90.0

    def test_old_predictions_expire(self) -> None:
        tracker = SyncTracker()
        # 5 correct, 5 wrong = 50%
        for _ in range(5):
            tracker.record_prediction("p1", "attack", "attack")
        for _ in range(5):
            tracker.record_prediction("p1", "attack", "defend")
        assert tracker.get_sync("p1") == 50.0
        # Add 5 more correct: pushes out the 5 correct from front,
        # now window is [wrong, wrong, wrong, wrong, wrong, correct, correct, correct, correct, correct]
        for _ in range(5):
            tracker.record_prediction("p1", "attack", "attack")
        assert tracker.get_sync("p1") == 50.0
