"""Tests for data.stat_diff — pure stat diff computation."""

from data.stat_diff import compute_diff


class TestNormalDiff:
    """Cycle 1: Normal case with improved, regressed, and neutral stats."""

    def test_improved_stat(self):
        lifetime = {"kills": 5.0}
        current = {"kills": 8.0}
        result = compute_diff(lifetime, current)
        assert result["kills"]["classification"] == "improved"
        assert result["kills"]["delta"] == 3.0
        assert result["kills"]["percentage"] == 60.0

    def test_regressed_stat(self):
        lifetime = {"damage_dealt": 100.0}
        current = {"damage_dealt": 70.0}
        result = compute_diff(lifetime, current)
        assert result["damage_dealt"]["classification"] == "regressed"
        assert result["damage_dealt"]["delta"] == -30.0
        assert result["damage_dealt"]["percentage"] == -30.0

    def test_neutral_stat(self):
        lifetime = {"wins": 3.0}
        current = {"wins": 3.0}
        result = compute_diff(lifetime, current)
        assert result["wins"]["classification"] == "neutral"
        assert result["wins"]["delta"] == 0.0
        assert result["wins"]["percentage"] == 0.0

    def test_mixed_stats(self):
        lifetime = {"kills": 5.0, "damage_dealt": 100.0, "wins": 3.0}
        current = {"kills": 8.0, "damage_dealt": 70.0, "wins": 3.0}
        result = compute_diff(lifetime, current)
        assert result["kills"]["classification"] == "improved"
        assert result["damage_dealt"]["classification"] == "regressed"
        assert result["wins"]["classification"] == "neutral"


class TestZeroLifetimeAverage:
    """Cycle 2: Zero lifetime average — guard against division by zero."""

    def test_zero_lifetime_improved(self):
        """Current > 0 with lifetime 0 should be improved, percentage 0."""
        result = compute_diff({"kills": 0.0}, {"kills": 5.0})
        assert result["kills"]["classification"] == "improved"
        assert result["kills"]["delta"] == 5.0
        assert result["kills"]["percentage"] is None  # undefined when lifetime is 0

    def test_zero_lifetime_neutral(self):
        """Both zero should be neutral."""
        result = compute_diff({"kills": 0.0}, {"kills": 0.0})
        assert result["kills"]["classification"] == "neutral"
        assert result["kills"]["delta"] == 0.0
        assert result["kills"]["percentage"] is None


class TestAsymmetricKeys:
    """Cycle 3: Stats present in one dict but not the other."""

    def test_stat_only_in_current(self):
        """New stat in current match, absent from lifetime -> treated as improved."""
        result = compute_diff({"kills": 5.0}, {"kills": 8.0, "headshots": 3.0})
        assert "headshots" in result
        assert result["headshots"]["classification"] == "improved"
        assert result["headshots"]["delta"] == 3.0
        # lifetime defaults to 0, so percentage is None (undefined)
        assert result["headshots"]["percentage"] is None

    def test_stat_only_in_lifetime(self):
        """Stat in lifetime but missing from current -> regressed (current=0)."""
        result = compute_diff({"kills": 5.0, "headshots": 2.0}, {"kills": 5.0})
        assert "headshots" in result
        assert result["headshots"]["classification"] == "regressed"
        assert result["headshots"]["delta"] == -2.0
        assert result["headshots"]["percentage"] == -100.0

    def test_no_overlapping_keys(self):
        """Completely disjoint stat sets."""
        result = compute_diff({"kills": 5.0}, {"headshots": 3.0})
        assert result["kills"]["classification"] == "regressed"
        assert result["kills"]["delta"] == -5.0
        assert result["headshots"]["classification"] == "improved"
        assert result["headshots"]["delta"] == 3.0


class TestFirstMatch:
    """Cycle 4: Empty or None lifetime_avg triggers first-match sentinel."""

    def test_none_lifetime_returns_first_match(self):
        current = {"kills": 5.0, "damage_dealt": 100.0}
        result = compute_diff(None, current)
        assert result["first_match"] is True
        assert result["kills"]["classification"] == "improved"
        assert result["kills"]["delta"] is None
        assert result["kills"]["percentage"] is None
        assert result["damage_dealt"]["classification"] == "improved"

    def test_empty_lifetime_returns_first_match(self):
        current = {"kills": 3.0}
        result = compute_diff({}, current)
        assert result["first_match"] is True
        assert result["kills"]["classification"] == "improved"
        assert result["kills"]["delta"] is None
        assert result["kills"]["percentage"] is None

    def test_both_empty_returns_first_match(self):
        """Both empty: first_match sentinel with no stat entries."""
        result = compute_diff({}, {})
        assert result["first_match"] is True
        assert len(result) == 1  # only the sentinel key

    def test_none_lifetime_empty_current(self):
        result = compute_diff(None, {})
        assert result["first_match"] is True
        assert len(result) == 1

    def test_first_match_includes_current_values(self):
        """First-match result must carry current stat values for viewer display."""
        result = compute_diff(None, {"kills": 5.0, "damage_dealt": 120.0})
        assert result["first_match"] is True
        assert result["kills"]["current"] == 5.0
        assert result["damage_dealt"]["current"] == 120.0

    def test_empty_lifetime_includes_current_values(self):
        """Same for empty dict lifetime."""
        result = compute_diff({}, {"kills": 3.0})
        assert result["first_match"] is True
        assert result["kills"]["current"] == 3.0


class TestZeroLifetimeIsNotFirstMatch:
    """All-zero lifetime is real history, not first match."""

    def test_all_zero_lifetime_not_first_match(self):
        """Lifetime with zero values should NOT trigger first_match."""
        result = compute_diff({"kills": 0.0}, {"kills": 5.0})
        assert "first_match" not in result
        assert result["kills"]["classification"] == "improved"
        assert result["kills"]["delta"] == 5.0
