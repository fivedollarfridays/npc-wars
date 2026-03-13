"""Tests for engine.bot_scanner.load_bot_module — shared bot module loading."""

import types

import pytest


VALID_BOT = '''\
BOT_NAME = "TestBot"
BOT_EMOJI = "T"

def decide(state):
    return ("rest",)
'''

DANGEROUS_BOT = '''\
import os
BOT_NAME = "Evil"
BOT_EMOJI = "E"
def decide(state): return ("rest",)
'''

SYNTAX_ERROR_BOT = "def bad syntax(:"


class TestLoadBotModule:
    """Test the shared load_bot_module helper."""

    def test_loads_valid_bot_returns_module(self, tmp_path):
        bot = tmp_path / "good.py"
        bot.write_text(VALID_BOT)
        from engine.bot_scanner import load_bot_module
        module = load_bot_module(str(bot))
        assert isinstance(module, types.ModuleType)
        assert module.BOT_NAME == "TestBot"
        assert callable(module.decide)

    def test_custom_module_name(self, tmp_path):
        bot = tmp_path / "good.py"
        bot.write_text(VALID_BOT)
        from engine.bot_scanner import load_bot_module
        module = load_bot_module(str(bot), module_name="custom_bot")
        assert module.__name__ == "custom_bot"

    def test_default_module_name_from_filename(self, tmp_path):
        bot = tmp_path / "my_bot.py"
        bot.write_text(VALID_BOT)
        from engine.bot_scanner import load_bot_module
        module = load_bot_module(str(bot))
        assert module.__name__ == "_bot_my_bot"

    def test_raises_value_error_on_scan_violations(self, tmp_path):
        bot = tmp_path / "evil.py"
        bot.write_text(DANGEROUS_BOT)
        from engine.bot_scanner import load_bot_module
        with pytest.raises(ValueError, match="Blocked import"):
            load_bot_module(str(bot))

    def test_raises_on_syntax_error(self, tmp_path):
        bot = tmp_path / "broken.py"
        bot.write_text(SYNTAX_ERROR_BOT)
        from engine.bot_scanner import load_bot_module
        with pytest.raises(ValueError, match="[Ss]yntax"):
            load_bot_module(str(bot))

    def test_raises_import_error_on_bad_path(self):
        from engine.bot_scanner import load_bot_module
        with pytest.raises((ImportError, OSError, ValueError)):
            load_bot_module("/nonexistent/path/bot.py")
