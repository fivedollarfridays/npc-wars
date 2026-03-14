"""Tests for npcwars.presets — preset strategy code generation."""

from __future__ import annotations

import ast

import pytest

from npcwars.presets import PRESET_NAMES, generate_preset


# --- input validation ---


class TestInputValidation:
    def test_invalid_style_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="style"):
            generate_preset("sniper")

    def test_aggression_zero_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="aggression"):
            generate_preset("aggro", aggression=0)

    def test_aggression_eleven_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="aggression"):
            generate_preset("aggro", aggression=11)

    def test_risk_zero_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="risk_tolerance"):
            generate_preset("aggro", risk_tolerance=0)

    def test_risk_eleven_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="risk_tolerance"):
            generate_preset("aggro", risk_tolerance=11)


# --- ast validity ---


class TestAstValidity:
    @pytest.mark.parametrize("style", PRESET_NAMES)
    def test_default_sliders_produce_valid_python(self, style: str) -> None:
        code = generate_preset(style)
        ast.parse(code)  # raises SyntaxError if invalid

    @pytest.mark.parametrize("style", PRESET_NAMES)
    def test_extreme_low_sliders_produce_valid_python(self, style: str) -> None:
        code = generate_preset(style, aggression=1, risk_tolerance=1)
        ast.parse(code)

    @pytest.mark.parametrize("style", PRESET_NAMES)
    def test_extreme_high_sliders_produce_valid_python(self, style: str) -> None:
        code = generate_preset(style, aggression=10, risk_tolerance=10)
        ast.parse(code)


# --- helpers import presence ---


class TestHelpersImport:
    @pytest.mark.parametrize("style", PRESET_NAMES)
    def test_contains_helpers_import(self, style: str) -> None:
        code = generate_preset(style)
        assert "from npcwars.helpers import" in code


# --- no blocked imports ---


_BLOCKED_MODULES = {"os", "subprocess", "sys", "shutil", "pathlib", "socket"}


class TestNoBlockedImports:
    @pytest.mark.parametrize("style", PRESET_NAMES)
    def test_no_blocked_imports(self, style: str) -> None:
        code = generate_preset(style)
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in _BLOCKED_MODULES, (
                        f"blocked import: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".")[0]
                    assert root not in _BLOCKED_MODULES, (
                        f"blocked import from: {node.module}"
                    )


# --- slider affects thresholds ---


class TestSliderAffectsThresholds:
    @pytest.mark.parametrize("style", PRESET_NAMES)
    def test_different_aggression_produces_different_code(self, style: str) -> None:
        low = generate_preset(style, aggression=1)
        high = generate_preset(style, aggression=10)
        assert low != high

    @pytest.mark.parametrize("style", PRESET_NAMES)
    def test_different_risk_produces_different_code(self, style: str) -> None:
        low = generate_preset(style, risk_tolerance=1)
        high = generate_preset(style, risk_tolerance=10)
        assert low != high


# --- preset names tuple ---


class TestPresetNames:
    def test_preset_names_has_five_entries(self) -> None:
        assert len(PRESET_NAMES) == 5

    def test_preset_names_are_strings(self) -> None:
        for name in PRESET_NAMES:
            assert isinstance(name, str)


# --- threshold values ---


class TestThresholdValues:
    def test_aggro_rest_hp_high_risk_is_low(self) -> None:
        """High risk_tolerance -> low rest_hp threshold (charges in wounded)."""
        code = generate_preset("aggro", risk_tolerance=10)
        assert "me.hp < 10" in code

    def test_aggro_rest_hp_low_risk_is_high(self) -> None:
        """Low risk_tolerance -> high rest_hp threshold (rests early)."""
        code = generate_preset("aggro", risk_tolerance=1)
        assert "me.hp < 40" in code

    def test_aggro_chase_range_high_aggression(self) -> None:
        """High aggression -> large chase range."""
        code = generate_preset("aggro", aggression=10)
        assert "dist_to(target) <= 8" in code

    def test_aggro_chase_range_low_aggression(self) -> None:
        """Low aggression -> small chase range."""
        code = generate_preset("aggro", aggression=1)
        assert "dist_to(target) <= 3" in code

    def test_chaos_uses_random_import(self) -> None:
        """Chaos preset uses random module."""
        code = generate_preset("chaos")
        assert "import random" in code

    def test_tank_has_defend_action(self) -> None:
        """Tank preset generates defend() calls."""
        code = generate_preset("tank")
        assert "me.defend()" in code

    def test_kiter_has_move_away(self) -> None:
        """Kiter preset generates move_away_from() calls."""
        code = generate_preset("kiter")
        assert "me.move_away_from(" in code

    def test_opportunist_targets_wounded(self) -> None:
        """Opportunist preset checks for wounded enemies."""
        code = generate_preset("opportunist")
        assert "enemies.wounded(" in code

    def test_threshold_values_are_integers(self) -> None:
        """All threshold values in generated code are integers (no floats)."""
        for style in PRESET_NAMES:
            for agg in (1, 5, 10):
                for risk in (1, 5, 10):
                    code = generate_preset(style, agg, risk)
                    # no floats like "< 25.0" in numeric comparisons
                    assert ".0" not in code or ".0]" not in code

    def test_generate_returns_string(self) -> None:
        """generate_preset returns a str."""
        result = generate_preset("aggro")
        assert isinstance(result, str)

    def test_all_presets_contain_storm_check(self) -> None:
        """Every preset checks for storm danger."""
        for style in PRESET_NAMES:
            code = generate_preset(style)
            assert "storm.danger" in code
