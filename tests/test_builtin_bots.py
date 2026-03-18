"""Tests for npcwars.builtin_bots package."""
from __future__ import annotations

import ast

import pytest

from agentgrounds.wars.builtin_bots import BUILTIN_NAMES, get_bot_source, list_builtin_bots


class TestListBuiltinBots:
    def test_returns_seven_items(self):
        result = list_builtin_bots()
        assert len(result) == 7

    def test_contains_all_expected_names(self):
        result = list_builtin_bots()
        expected = {
            "example_aggro",
            "example_tank",
            "example_kiter",
            "example_random",
            "example_vibes",
            "starter",
            "template",
        }
        assert set(result) == expected

    def test_returns_list_type(self):
        assert isinstance(list_builtin_bots(), list)


class TestGetBotSource:
    def test_template_contains_bot_name(self):
        source = get_bot_source("template")
        assert "BOT_NAME" in source

    def test_aggro_contains_decide(self):
        source = get_bot_source("example_aggro")
        assert "def decide" in source

    def test_nonexistent_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown built-in bot"):
            get_bot_source("nonexistent")

    @pytest.mark.parametrize("name", BUILTIN_NAMES)
    def test_each_bot_source_parses(self, name: str):
        source = get_bot_source(name)
        ast.parse(source)  # should not raise

    @pytest.mark.parametrize("name", BUILTIN_NAMES)
    def test_each_bot_source_is_string(self, name: str):
        assert isinstance(get_bot_source(name), str)

    def test_goose_loose_not_included(self):
        assert "goose_loose" not in BUILTIN_NAMES
