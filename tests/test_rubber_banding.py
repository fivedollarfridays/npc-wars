"""Tests for the rubber-banding difficulty system."""

from __future__ import annotations

from unittest.mock import MagicMock

from engine.watcher_brain import (
    HumanPerformance,
    apply_accuracy_cap,
    get_accuracy_cap,
)


# --- Cycle 1: get_accuracy_cap tiers ---


class TestGetAccuracyCap:
    """Test accuracy cap tiers based on human performance."""

    def test_losing_human_cap(self) -> None:
        """Losing human (hp_ratio < 0.3, kills == 0) -> 0.60 cap."""
        perf = HumanPerformance(hp_ratio=0.2, kills=0, rounds_survived=5)
        assert get_accuracy_cap(perf) == 0.60

    def test_losing_human_edge_hp(self) -> None:
        """hp_ratio exactly 0.29 with 0 kills is still losing."""
        perf = HumanPerformance(hp_ratio=0.29, kills=0, rounds_survived=3)
        assert get_accuracy_cap(perf) == 0.60

    def test_even_match_low_hp(self) -> None:
        """Even match: hp_ratio < 0.5 with kills=1 -> 0.75 cap."""
        perf = HumanPerformance(hp_ratio=0.4, kills=1, rounds_survived=8)
        assert get_accuracy_cap(perf) == 0.75

    def test_even_match_moderate_hp_low_kills(self) -> None:
        """Even match: hp_ratio=0.5 but kills <= 1 -> 0.75 cap."""
        perf = HumanPerformance(hp_ratio=0.5, kills=1, rounds_survived=10)
        assert get_accuracy_cap(perf) == 0.75

    def test_even_match_hp_below_half_with_kills(self) -> None:
        """Even match: hp_ratio=0.3 with kills=1 -> 0.75 (not losing, has a kill)."""
        perf = HumanPerformance(hp_ratio=0.3, kills=1, rounds_survived=6)
        assert get_accuracy_cap(perf) == 0.75

    def test_winning_human_cap(self) -> None:
        """Winning human (hp_ratio >= 0.5 and kills >= 2) -> 0.90 cap."""
        perf = HumanPerformance(hp_ratio=0.5, kills=2, rounds_survived=12)
        assert get_accuracy_cap(perf) == 0.90

    def test_winning_human_high_hp(self) -> None:
        """Winning but not dominating: hp_ratio=0.65, kills=2 -> 0.90."""
        perf = HumanPerformance(hp_ratio=0.65, kills=2, rounds_survived=10)
        assert get_accuracy_cap(perf) == 0.90

    def test_dominating_human_cap(self) -> None:
        """Dominating human (hp_ratio >= 0.7 and kills >= 3) -> 0.95 cap."""
        perf = HumanPerformance(hp_ratio=0.7, kills=3, rounds_survived=15)
        assert get_accuracy_cap(perf) == 0.95

    def test_dominating_human_very_strong(self) -> None:
        """Dominating: hp_ratio=1.0, kills=5 -> 0.95."""
        perf = HumanPerformance(hp_ratio=1.0, kills=5, rounds_survived=20)
        assert get_accuracy_cap(perf) == 0.95


# --- Cycle 2: apply_accuracy_cap ---


class TestApplyAccuracyCap:
    """Test probabilistic accuracy cap application."""

    def test_within_cap_returns_counter(self) -> None:
        """When rng.random() <= cap, return counter_action unchanged."""
        rng = MagicMock()
        rng.random.return_value = 0.50  # <= 0.60 cap
        counter = ("attack", "north")
        all_actions = ["move", "attack", "defend", "rest"]
        result = apply_accuracy_cap(counter, 0.60, all_actions, rng)
        assert result == ("attack", "north")

    def test_exactly_at_cap_returns_counter(self) -> None:
        """When rng.random() == cap exactly, return counter_action."""
        rng = MagicMock()
        rng.random.return_value = 0.75
        counter = ("defend",)
        all_actions = ["move", "attack", "defend", "rest"]
        result = apply_accuracy_cap(counter, 0.75, all_actions, rng)
        assert result == ("defend",)

    def test_above_cap_returns_random_action(self) -> None:
        """When rng.random() > cap, return a random action from all_actions."""
        rng = MagicMock()
        rng.random.return_value = 0.85  # > 0.60 cap
        rng.choice.return_value = "rest"
        counter = ("attack", "north")
        all_actions = ["move", "attack", "defend", "rest"]
        result = apply_accuracy_cap(counter, 0.60, all_actions, rng)
        assert result == ("rest",)
        rng.choice.assert_called_once_with(all_actions)

    def test_cap_zero_always_random(self) -> None:
        """Cap of 0.0 always returns random action (any rng > 0)."""
        rng = MagicMock()
        rng.random.return_value = 0.01
        rng.choice.return_value = "move"
        counter = ("attack", "south")
        all_actions = ["move", "attack"]
        result = apply_accuracy_cap(counter, 0.0, all_actions, rng)
        assert result == ("move",)

    def test_cap_one_always_counter(self) -> None:
        """Cap of 1.0 always returns counter action (rng <= 1.0)."""
        rng = MagicMock()
        rng.random.return_value = 0.999
        counter = ("dash", "east")
        all_actions = ["move", "attack", "dash"]
        result = apply_accuracy_cap(counter, 1.0, all_actions, rng)
        assert result == ("dash", "east")
