"""Tests for bots/starter.py — the guided tutorial bot."""
from __future__ import annotations

import importlib
from pathlib import Path

from scripts.validate_bot import validate_bot
from tests.conftest import bot_config

STARTER_PATH = str(Path(__file__).resolve().parent.parent / "bots" / "starter.py")
BUILTIN_STARTER_PATH = str(
    Path(__file__).resolve().parent.parent
    / "npcwars"
    / "builtin_bots"
    / "starter.py"
)


def _load_starter():
    """Import bots/starter.py as a module."""
    spec = importlib.util.spec_from_file_location("starter", STARTER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestStarterPassesValidation:
    def test_bots_starter_validates(self):
        ok, errors = validate_bot(STARTER_PATH)
        assert ok is True, f"Validation errors: {errors}"

    def test_builtin_starter_validates(self):
        ok, errors = validate_bot(BUILTIN_STARTER_PATH)
        assert ok is True, f"Validation errors: {errors}"


class TestStarterHasTodoComments:
    def test_at_least_seven_todos(self):
        source = Path(STARTER_PATH).read_text()
        todo_count = source.count("TODO")
        assert todo_count >= 7, f"Expected >= 7 TODOs, found {todo_count}"

    def test_has_priority_comments(self):
        source = Path(STARTER_PATH).read_text()
        for i in range(1, 9):
            assert f"PRIORITY {i}" in source, f"Missing PRIORITY {i} comment"


class TestStarterUsesHelpersDsl:
    def test_imports_me_enemies_storm(self):
        source = Path(STARTER_PATH).read_text()
        assert "from npcwars.helpers import Me, Enemies, Storm" in source

    def test_constructs_helpers(self):
        source = Path(STARTER_PATH).read_text()
        assert "Me(state)" in source
        assert "Enemies(state)" in source
        assert "Storm(state)" in source


class TestStarterCompetitive:
    """Run seeded matches to verify the starter bot wins at least 1 out of 10."""

    def test_wins_at_least_one_match(self):
        from engine.game import run_match

        starter = _load_starter()

        def move_south(state):
            return ("move", "south")

        wins = 0
        for seed in range(10):
            configs = [
                bot_config("Starter", "\U0001f31f", starter.decide),
                bot_config("Southie1", "\U0001f3c3", move_south),
                bot_config("Southie2", "\U0001f6b6", move_south),
                bot_config("Rester", "\U0001f4a4", lambda s: ("rest",)),
            ]
            data = run_match(configs, match_id=seed, seed=seed)
            if data["winner"] == "\U0001f31f":
                wins += 1

        assert wins >= 1, f"Starter won {wins}/10 matches -- expected at least 1"


class TestStarterMetadata:
    def test_has_bot_name(self):
        mod = _load_starter()
        assert mod.BOT_NAME == "Starter"

    def test_has_bot_emoji(self):
        mod = _load_starter()
        assert hasattr(mod, "BOT_EMOJI")

    def test_has_bot_bio(self):
        mod = _load_starter()
        assert hasattr(mod, "BOT_BIO")
        assert "TODO" in mod.BOT_BIO.lower() or len(mod.BOT_BIO) > 5


class TestStarterInBuiltinBots:
    def test_starter_listed_in_builtin_names(self):
        from npcwars.builtin_bots import BUILTIN_NAMES

        assert "starter" in BUILTIN_NAMES

    def test_get_bot_source_returns_starter(self):
        from npcwars.builtin_bots import get_bot_source

        source = get_bot_source("starter")
        assert "BOT_NAME" in source
        assert "def decide" in source
