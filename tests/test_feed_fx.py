"""Tests for differentiated FX in kill-feed formatters (T25.3)."""
from __future__ import annotations

from agentgrounds.wars.cli.feed import format_feed_event


class TestFeedHitFx:
    def test_hit_contains_explosion_emoji(self) -> None:
        evt = {"type": "hit", "attacker": "\U0001f916", "target": "\U0001f3af", "damage": 25}
        line = format_feed_event(evt, 5)
        assert "\U0001f4a5" in line  # 💥

    def test_hit_contains_damage(self) -> None:
        evt = {"type": "hit", "attacker": "\U0001f916", "target": "\U0001f3af", "damage": 25}
        line = format_feed_event(evt, 5)
        assert "-25hp" in line


class TestFeedKillFx:
    def test_kill_contains_skull_fire_emoji(self) -> None:
        evt = {"type": "kill", "attacker": "\U0001f916", "victim": "\U0001f3af"}
        line = format_feed_event(evt, 5)
        assert "\U0001f480\U0001f525" in line  # 💀🔥

    def test_kill_contains_eliminated(self) -> None:
        evt = {"type": "kill", "attacker": "\U0001f916", "victim": "\U0001f3af"}
        line = format_feed_event(evt, 5)
        assert "eliminated" in line


class TestFeedMissFx:
    def test_miss_contains_dash_emoji(self) -> None:
        evt = {"type": "miss", "attacker": "\U0001f916", "direction": "east"}
        line = format_feed_event(evt, 5)
        assert "\U0001f4a8" in line  # 💨

    def test_miss_contains_missed(self) -> None:
        evt = {"type": "miss", "attacker": "\U0001f916", "direction": "east"}
        line = format_feed_event(evt, 5)
        assert "missed" in line


class TestFeedDefendFx:
    def test_defend_shows_defending(self) -> None:
        evt = {"type": "defend", "emoji": "\U0001f422"}
        line = format_feed_event(evt, 5)
        assert "defending" in line

    def test_defend_blocked_shows_blocked(self) -> None:
        evt = {"type": "defend", "emoji": "\U0001f422", "blocked": True}
        line = format_feed_event(evt, 5)
        assert "blocked!" in line
        assert "\u2728" in line  # ✨
