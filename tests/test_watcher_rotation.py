"""Tests for Watcher adaptive target rotation."""

from __future__ import annotations

from engine.watcher_brain import SyncTracker, select_target


class TestSelectTarget:
    """Tests for select_target() target rotation logic."""

    def test_empty_human_list_returns_none(self) -> None:
        tracker = SyncTracker()
        assert select_target(tracker, []) is None

    def test_single_human_always_targeted(self) -> None:
        tracker = SyncTracker()
        # Even with 0 sync, the sole human is the target
        assert select_target(tracker, ["Alice"]) == "Alice"

    def test_targets_human_with_higher_sync(self) -> None:
        tracker = SyncTracker()
        # Make Bob more predictable than Alice
        for _ in range(5):
            tracker.record_prediction("Bob", "attack", "attack")   # correct
            tracker.record_prediction("Alice", "attack", "defend")  # wrong
        assert select_target(tracker, ["Alice", "Bob"]) == "Bob"

    def test_switches_target_when_sync_changes(self) -> None:
        tracker = SyncTracker()
        # Initially Bob is more predictable
        for _ in range(5):
            tracker.record_prediction("Bob", "attack", "attack")
            tracker.record_prediction("Alice", "attack", "defend")
        assert select_target(tracker, ["Alice", "Bob"]) == "Bob"

        # Now Alice becomes more predictable
        for _ in range(10):
            tracker.record_prediction("Alice", "move", "move")
            tracker.record_prediction("Bob", "attack", "defend")
        assert select_target(tracker, ["Alice", "Bob"]) == "Alice"

    def test_equal_sync_breaks_tie_by_sorted_order(self) -> None:
        tracker = SyncTracker()
        # Both have identical sync (0.0 — no data)
        result = select_target(tracker, ["Zara", "Amy"])
        assert result == "Amy"  # alphabetically first

        # Both with identical non-zero sync
        for _ in range(3):
            tracker.record_prediction("Zara", "attack", "attack")
            tracker.record_prediction("Amy", "attack", "attack")
        assert tracker.get_sync("Zara") == tracker.get_sync("Amy")
        result = select_target(tracker, ["Zara", "Amy"])
        assert result == "Amy"

    def test_switching_target_preserves_pattern_data(self) -> None:
        tracker = SyncTracker()
        # Build up data for both players
        for _ in range(5):
            tracker.record_prediction("Alice", "attack", "attack")
            tracker.record_prediction("Bob", "move", "move")

        alice_sync_before = tracker.get_sync("Alice")
        bob_sync_before = tracker.get_sync("Bob")

        # Select target (triggers rotation logic)
        select_target(tracker, ["Alice", "Bob"])

        # Pattern data for both players is unchanged
        assert tracker.get_sync("Alice") == alice_sync_before
        assert tracker.get_sync("Bob") == bob_sync_before
