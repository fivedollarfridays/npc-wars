"""Tests for tactical/ability/evolve feed formatters and overlay FX."""

from __future__ import annotations

from agentgrounds.wars.cli.feed import format_feed_event
from agentgrounds.wars.cli.overlay import build_combat_overlay


# -- Feed formatter tests --


class TestTacticalActivateFeed:
    """Feed formatter for tactical_activate events."""

    def test_basic_format(self) -> None:
        evt = {
            "type": "tactical_activate",
            "emoji": "\U0001f916",
            "tactical": "battle_cry",
            "effect": "1.5x damage this round",
        }
        result = format_feed_event(evt, 3)
        assert result is not None
        assert "R3" in result
        assert "\U0001f916" in result
        assert "\u26a1" in result  # lightning bolt
        assert "battle_cry" in result
        assert "1.5x damage" in result

    def test_fortify_effect(self) -> None:
        evt = {
            "type": "tactical_activate",
            "emoji": "\U0001f60e",
            "tactical": "fortify",
            "effect": "+5 DR, +10 temp HP",
        }
        result = format_feed_event(evt, 7)
        assert result is not None
        assert "+5 DR" in result


class TestAbilityDamageFeed:
    """Feed formatter for ability_damage events."""

    def test_basic_format(self) -> None:
        evt = {
            "type": "ability_damage",
            "emoji": "\U0001f916",
            "target": "\U0001f3af",
            "ability": "Fireball",
            "damage": 30,
            "hp_before": 80.0,
        }
        result = format_feed_event(evt, 5)
        assert result is not None
        assert "R5" in result
        assert "\U0001f916" in result
        assert "\U0001f52e" in result  # crystal ball
        assert "Fireball" in result
        assert "\U0001f3af" in result
        assert "-30hp" in result


class TestAbilityHealFeed:
    """Feed formatter for ability_heal events."""

    def test_basic_format(self) -> None:
        evt = {
            "type": "ability_heal",
            "emoji": "\U0001f916",
            "ability": "Heal",
            "healed": 20.0,
        }
        result = format_feed_event(evt, 4)
        assert result is not None
        assert "R4" in result
        assert "\U0001f49a" in result  # green heart
        assert "Heal" in result
        assert "+20" in result


class TestAbilityShieldFeed:
    """Feed formatter for ability_shield events."""

    def test_basic_format(self) -> None:
        evt = {
            "type": "ability_shield",
            "emoji": "\U0001f916",
            "ability": "Shield",
            "dr": 15,
            "rounds": 2,
        }
        result = format_feed_event(evt, 6)
        assert result is not None
        assert "R6" in result
        assert "\U0001f6e1\ufe0f" in result  # shield
        assert "Shield" in result
        assert "+15" in result
        assert "DR" in result


class TestAbilitySlowFeed:
    """Feed formatter for ability_slow events."""

    def test_basic_format(self) -> None:
        evt = {
            "type": "ability_slow",
            "emoji": "\U0001f916",
            "target": "\U0001f3af",
            "ability": "Slow",
            "slow": 10,
            "rounds": 3,
        }
        result = format_feed_event(evt, 2)
        assert result is not None
        assert "R2" in result
        assert "\U0001f40c" in result  # snail
        assert "Slow" in result
        assert "\U0001f3af" in result
        assert "-10" in result


class TestEvolveFeed:
    """Feed formatter for evolve events."""

    def test_basic_format(self) -> None:
        evt = {
            "type": "evolve",
            "emoji": "\U0001f916",
            "adaptations": {"potency": 5},
        }
        result = format_feed_event(evt, 8)
        assert result is not None
        assert "R8" in result
        assert "\U0001f9ec" in result  # dna
        assert "evolved" in result

    def test_unknown_type_returns_none(self) -> None:
        evt = {"type": "not_a_real_event"}
        result = format_feed_event(evt, 1)
        assert result is None


# -- Overlay FX tests --


class TestTacticalOverlay:
    """Overlay FX for tactical_activate events."""

    def test_lightning_on_bot_tile(self) -> None:
        positions = [{"emoji": "\U0001f916", "x": 3, "y": 4, "alive": True}]
        events = [
            {"type": "tactical_activate", "emoji": "\U0001f916",
             "tactical": "battle_cry", "effect": "1.5x damage"},
        ]
        overlay = build_combat_overlay(positions, events)
        assert (3, 4) in overlay
        assert "\u26a1" in overlay[(3, 4)]


class TestAbilityDamageOverlay:
    """Overlay FX for ability_damage on target tile."""

    def test_crystal_on_target_tile(self) -> None:
        positions = [
            {"emoji": "\U0001f916", "x": 2, "y": 2, "alive": True},
            {"emoji": "\U0001f3af", "x": 4, "y": 2, "alive": True},
        ]
        events = [
            {"type": "ability_damage", "emoji": "\U0001f916",
             "target": "\U0001f3af", "ability": "Fireball",
             "damage": 30, "hp_before": 80.0},
        ]
        overlay = build_combat_overlay(positions, events)
        assert (4, 2) in overlay
        assert "\U0001f52e" in overlay[(4, 2)]


class TestEvolveOverlay:
    """Overlay FX for evolve events."""

    def test_dna_on_bot_tile(self) -> None:
        positions = [{"emoji": "\U0001f916", "x": 5, "y": 5, "alive": True}]
        events = [
            {"type": "evolve", "emoji": "\U0001f916",
             "adaptations": {"potency": 5}},
        ]
        overlay = build_combat_overlay(positions, events)
        assert (5, 5) in overlay
        assert "\U0001f9ec" in overlay[(5, 5)]
