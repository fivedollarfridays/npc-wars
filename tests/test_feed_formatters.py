"""Tests for crit/attack-miss feed formatters (T28.7)."""
from __future__ import annotations

from agentgrounds.wars.cli.feed import _FORMATTERS, format_feed_event


class TestHitCrit:
    def test_hit_normal_no_crit(self) -> None:
        evt = {"type": "hit", "attacker": "\U0001f916", "target": "\U0001f422", "damage": 25}
        line = format_feed_event(evt, 5)
        assert line is not None
        assert "CRIT" not in line

    def test_hit_with_crit(self) -> None:
        evt = {
            "type": "hit",
            "attacker": "\U0001f916",
            "target": "\U0001f422",
            "damage": 37,
            "is_crit": True,
        }
        line = format_feed_event(evt, 5)
        assert line is not None
        assert "CRIT" in line
        assert "-37hp" in line

    def test_hit_crit_false_no_indicator(self) -> None:
        evt = {
            "type": "hit",
            "attacker": "\U0001f916",
            "target": "\U0001f422",
            "damage": 25,
            "is_crit": False,
        }
        line = format_feed_event(evt, 5)
        assert line is not None
        assert "CRIT" not in line


class TestRangedHitCrit:
    def test_ranged_hit_with_crit(self) -> None:
        evt = {
            "type": "ranged_hit",
            "attacker": "\U0001f916",
            "target": "\U0001f422",
            "damage": 40,
            "is_crit": True,
        }
        line = format_feed_event(evt, 5)
        assert line is not None
        assert "CRIT" in line
        assert "-40hp" in line

    def test_ranged_hit_no_crit(self) -> None:
        evt = {"type": "ranged_hit", "attacker": "\U0001f916", "target": "\U0001f422", "damage": 20}
        line = format_feed_event(evt, 5)
        assert line is not None
        assert "CRIT" not in line


class TestAttackMiss:
    def test_attack_miss_formatted(self) -> None:
        evt = {
            "type": "attack_miss",
            "attacker": "\U0001f916",
            "target": "\U0001f422",
            "roll": 5,
            "modifier": 2,
            "ac": 14,
        }
        line = format_feed_event(evt, 5)
        assert line is not None
        assert "\U0001f916" in line
        assert "\U0001f422" in line
        assert "dodged" in line

    def test_attack_miss_registered(self) -> None:
        assert "attack_miss" in _FORMATTERS


class TestRangedAttackMiss:
    def test_ranged_attack_miss_formatted(self) -> None:
        evt = {
            "type": "ranged_attack_miss",
            "attacker": "\U0001f916",
            "target": "\U0001f422",
            "roll": 3,
            "modifier": 1,
            "ac": 12,
        }
        line = format_feed_event(evt, 5)
        assert line is not None
        assert "\U0001f916" in line
        assert "\U0001f422" in line
        assert "dodged" in line

    def test_ranged_attack_miss_registered(self) -> None:
        assert "ranged_attack_miss" in _FORMATTERS
