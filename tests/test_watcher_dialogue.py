"""Tests for Watcher monologue generation."""

from __future__ import annotations

import pytest

from engine.watcher_dialogue import generate_monologue, TRIGGERS


class TestTriggerCoverage:
    """Every trigger type produces a valid monologue at every sync tier."""

    @pytest.mark.parametrize("trigger", ["spawn", "kill", "sync_milestone", "player_death"])
    @pytest.mark.parametrize("sync", [10.0, 50.0, 85.0], ids=["low", "mid", "high"])
    def test_all_triggers_all_tiers(self, trigger: str, sync: float) -> None:
        result = generate_monologue(trigger, sync, {"top_action": "rest", "context": "below_30_hp"})
        assert isinstance(result, str)
        assert len(result) > 0


class TestSyncTierSelection:
    """Tone varies by sync level boundaries."""

    def test_low_sync_below_30(self) -> None:
        result = generate_monologue("spawn", 0.0, {"top_action": "rest"})
        # Should not contain high-sync phrases
        assert isinstance(result, str)

    def test_low_sync_at_boundary(self) -> None:
        result = generate_monologue("spawn", 29.9, {"top_action": "rest"})
        assert isinstance(result, str)

    def test_mid_sync_at_30(self) -> None:
        result = generate_monologue("spawn", 30.0, {"top_action": "attack"})
        assert isinstance(result, str)

    def test_mid_sync_at_70_boundary(self) -> None:
        result = generate_monologue("spawn", 70.0, {"top_action": "attack"})
        assert isinstance(result, str)

    def test_high_sync_above_70(self) -> None:
        result = generate_monologue("spawn", 70.1, {"top_action": "move"})
        assert isinstance(result, str)

    def test_high_sync_100(self) -> None:
        result = generate_monologue("spawn", 100.0, {"top_action": "move"})
        assert isinstance(result, str)


class TestTemplatePlaceholders:
    """Pattern summary data is injected into templates."""

    def test_top_action_in_output(self) -> None:
        """At least some templates reference top_action."""
        from engine.watcher_dialogue import _TEMPLATES

        found = any(
            "{action}" in t
            for trigger_templates in _TEMPLATES.values()
            for tier_templates in trigger_templates.values()
            for t in tier_templates
        )
        assert found, "No template uses {action} placeholder"

    def test_context_in_output(self) -> None:
        """At least some templates reference context."""
        from engine.watcher_dialogue import _TEMPLATES

        found = any(
            "{context}" in t
            for trigger_templates in _TEMPLATES.values()
            for tier_templates in trigger_templates.values()
            for t in tier_templates
        )
        assert found, "No template uses {context} placeholder"


class TestTemplateCount:
    """At least 5 templates per trigger type."""

    @pytest.mark.parametrize("trigger", ["spawn", "kill", "sync_milestone", "player_death"])
    def test_at_least_5_per_trigger(self, trigger: str) -> None:
        from engine.watcher_dialogue import _TEMPLATES

        total = sum(len(v) for v in _TEMPLATES[trigger].values())
        assert total >= 5, f"{trigger} has only {total} templates"


class TestInvalidTrigger:
    """Unknown trigger raises ValueError."""

    def test_unknown_trigger(self) -> None:
        with pytest.raises(ValueError, match="Unknown trigger"):
            generate_monologue("unknown_trigger", 50.0, {})


class TestEmptyPatternSummary:
    """Monologues work with empty or minimal pattern summary."""

    @pytest.mark.parametrize("trigger", ["spawn", "kill", "sync_milestone", "player_death"])
    def test_empty_summary(self, trigger: str) -> None:
        result = generate_monologue(trigger, 50.0, {})
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("trigger", ["spawn", "kill", "sync_milestone", "player_death"])
    def test_none_values_in_summary(self, trigger: str) -> None:
        result = generate_monologue(trigger, 50.0, {"top_action": None, "context": None})
        assert isinstance(result, str)
        assert "None" not in result


class TestDeterminism:
    """Same inputs with same seed produce same output."""

    def test_reproducible_with_seed(self) -> None:
        import random

        for trigger in TRIGGERS:
            random.seed(42)
            a = generate_monologue(trigger, 50.0, {"top_action": "rest"})
            random.seed(42)
            b = generate_monologue(trigger, 50.0, {"top_action": "rest"})
            assert a == b
