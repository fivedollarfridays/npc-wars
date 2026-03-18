"""Tests for the npcwars validate CLI command (T14.6)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)

_VALID_BOT = '''\
BOT_NAME = "TestBot"
BOT_EMOJI = "X"
BOT_BIO = "test"
BOT_AUTHOR = "test"

def decide(state):
    return ("rest",)
'''

_INVALID_SYNTAX_BOT = '''\
BOT_NAME = "BadBot"
def decide(state
    return ("rest",)
'''


def _run_cli(*args: str, timeout: float = 30) -> subprocess.CompletedProcess[str]:
    """Run ``npcwars validate`` via subprocess."""
    return subprocess.run(
        [sys.executable, "-m", "agentgrounds.wars.cli", "validate", *args],
        capture_output=True,
        text=True,
        cwd=_PROJECT_ROOT,
        timeout=timeout,
    )


class TestValidateHelp:
    """--help flag."""

    def test_help_exits_zero(self) -> None:
        result = _run_cli("--help")
        assert result.returncode == 0


class TestValidateValidBot:
    """Valid bot files pass validation."""

    def test_valid_bot_exits_zero(self, tmp_path: Path) -> None:
        bot = tmp_path / "good_bot.py"
        bot.write_text(_VALID_BOT)
        result = _run_cli(str(bot))
        assert result.returncode == 0

    def test_valid_bot_output_contains_pass(self, tmp_path: Path) -> None:
        bot = tmp_path / "good_bot.py"
        bot.write_text(_VALID_BOT)
        result = _run_cli(str(bot))
        assert "PASS" in result.stdout


class TestValidateInvalidBot:
    """Invalid bot files fail validation."""

    def test_bad_syntax_exits_one(self, tmp_path: Path) -> None:
        bot = tmp_path / "bad_bot.py"
        bot.write_text(_INVALID_SYNTAX_BOT)
        result = _run_cli(str(bot))
        assert result.returncode == 1

    def test_missing_file_exits_one(self, tmp_path: Path) -> None:
        result = _run_cli(str(tmp_path / "nonexistent.py"))
        assert result.returncode == 1

    def test_bad_syntax_output_contains_fail(self, tmp_path: Path) -> None:
        bot = tmp_path / "bad_bot.py"
        bot.write_text(_INVALID_SYNTAX_BOT)
        result = _run_cli(str(bot))
        assert "FAIL" in result.stdout


class TestValidateMultipleBots:
    """Multiple bot files in one invocation."""

    def test_multiple_valid_all_pass(self, tmp_path: Path) -> None:
        bot1 = tmp_path / "bot1.py"
        bot2 = tmp_path / "bot2.py"
        bot1.write_text(_VALID_BOT)
        bot2.write_text(_VALID_BOT.replace("TestBot", "TestBot2"))
        result = _run_cli(str(bot1), str(bot2))
        assert result.returncode == 0

    def test_one_invalid_among_valid_fails(self, tmp_path: Path) -> None:
        good = tmp_path / "good.py"
        bad = tmp_path / "bad.py"
        good.write_text(_VALID_BOT)
        bad.write_text(_INVALID_SYNTAX_BOT)
        result = _run_cli(str(good), str(bad))
        assert result.returncode == 1
