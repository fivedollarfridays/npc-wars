"""Integration tests for bot_scanner with loader.py and validate_bot.py."""

import os

from engine.bot_scanner import scan_bot_file


class TestExampleBotsScan:
    """All shipped example bots must pass the scanner."""

    _BOTS_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bots"
    )

    def _bot_files(self) -> list[str]:
        files = []
        for name in sorted(os.listdir(self._BOTS_DIR)):
            if name.endswith(".py") and not name.startswith("_") and name != "template.py":
                files.append(os.path.join(self._BOTS_DIR, name))
        return files

    def test_all_example_bots_pass(self):
        """Every shipped bot must have zero violations."""
        for path in self._bot_files():
            violations = scan_bot_file(path)
            assert violations == [], f"{os.path.basename(path)}: {violations}"

    def test_at_least_five_bots_checked(self):
        """Sanity: we should have at least 5 example bots."""
        assert len(self._bot_files()) >= 5


class TestLoaderIntegration:
    """Loader should reject bots with blocked imports."""

    def test_loader_skips_bad_bot(self, tmp_path):
        """A bot with 'import os' should be skipped by the loader."""
        bot = tmp_path / "evil_bot.py"
        bot.write_text(
            "import os\n"
            "BOT_NAME = 'Evil'\n"
            "BOT_EMOJI = '😈'\n"
            "BOT_BIO = 'hacker'\n"
            "BOT_AUTHOR = 'test'\n"
            "def decide(state): return ('rest',)\n"
        )
        # Also need a clean bot so loader returns something
        clean = tmp_path / "clean_bot.py"
        clean.write_text(
            "import random\n"
            "BOT_NAME = 'Clean'\n"
            "BOT_EMOJI = '✅'\n"
            "BOT_BIO = 'good bot'\n"
            "BOT_AUTHOR = 'test'\n"
            "def decide(state): return ('rest',)\n"
        )
        from engine.loader import load_bots
        bots = load_bots(str(tmp_path))
        names = [b["name"] for b in bots]
        assert "Evil" not in names
        assert "Clean" in names

    def test_loader_loads_clean_bot(self, tmp_path):
        """A bot with only safe imports should load fine."""
        bot = tmp_path / "safe_bot.py"
        bot.write_text(
            "import random\n"
            "BOT_NAME = 'Safe'\n"
            "BOT_EMOJI = '🟢'\n"
            "BOT_BIO = 'safe'\n"
            "BOT_AUTHOR = 'test'\n"
            "def decide(state): return ('rest',)\n"
        )
        from engine.loader import load_bots
        bots = load_bots(str(tmp_path))
        assert len(bots) == 1
        assert bots[0]["name"] == "Safe"


class TestValidateBotIntegration:
    """validate_bot.py should call scanner and report violations."""

    def test_validate_bot_rejects_blocked_import(self, tmp_path):
        """validate_bot() should fail for a bot with blocked imports."""
        bot = tmp_path / "bad.py"
        bot.write_text(
            "import subprocess\n"
            "BOT_NAME = 'Bad'\n"
            "BOT_EMOJI = '💀'\n"
            "def decide(state): return ('rest',)\n"
        )
        from scripts.validate_bot import validate_bot
        ok, errors = validate_bot(str(bot))
        assert not ok
        assert any("subprocess" in e.lower() or "blocked" in e.lower() for e in errors)

    def test_validate_bot_passes_clean(self, tmp_path):
        """validate_bot() should pass for a clean bot."""
        bot = tmp_path / "good.py"
        bot.write_text(
            "import random\n"
            "BOT_NAME = 'Good'\n"
            "BOT_EMOJI = '🟢'\n"
            "def decide(state): return ('rest',)\n"
        )
        from scripts.validate_bot import validate_bot
        ok, errors = validate_bot(str(bot))
        assert ok
        assert errors == []
