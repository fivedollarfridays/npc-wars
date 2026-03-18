"""Tests for wizard.py — interactive bot generator CLI."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from agentgrounds.wars.presets import PRESET_NAMES
from wizard import build_bot_source, validate_inputs

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)


# --- Cycle 1: non-interactive generates valid bot file ---


class TestNonInteractiveGeneration:
    """Non-interactive mode generates a valid bot file with correct metadata."""

    def test_generates_bot_file(self, tmp_path: Path) -> None:
        """Non-interactive mode creates the bot file in output dir."""
        result = subprocess.run(
            [
                sys.executable, "wizard.py",
                "--non-interactive",
                "--name", "TestBot",
                "--emoji", "T",
                "--style", "aggro",
                "--output-dir", str(tmp_path),
            ],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "testbot.py").exists()

    def test_bot_file_has_correct_bot_name(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [
                sys.executable, "wizard.py",
                "--non-interactive",
                "--name", "Cognify",
                "--emoji", "B",
                "--style", "aggro",
                "--output-dir", str(tmp_path),
            ],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0, result.stderr
        content = (tmp_path / "cognify.py").read_text()
        assert "BOT_NAME = 'Cognify'" in content or 'BOT_NAME = "Cognify"' in content

    def test_bot_file_has_correct_emoji(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [
                sys.executable, "wizard.py",
                "--non-interactive",
                "--name", "EmoBot",
                "--emoji", "Z",
                "--style", "tank",
                "--output-dir", str(tmp_path),
            ],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0, result.stderr
        content = (tmp_path / "emobot.py").read_text()
        assert "BOT_EMOJI = 'Z'" in content or 'BOT_EMOJI = "Z"' in content

    def test_bot_file_has_bio_and_author(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [
                sys.executable, "wizard.py",
                "--non-interactive",
                "--name", "MetaBot",
                "--emoji", "M",
                "--style", "kiter",
                "--bio", "a sneaky one",
                "--author", "kevin",
                "--output-dir", str(tmp_path),
            ],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0, result.stderr
        content = (tmp_path / "metabot.py").read_text()
        assert "BOT_BIO = 'a sneaky one'" in content or 'BOT_BIO = "a sneaky one"' in content
        assert "BOT_AUTHOR = 'kevin'" in content or 'BOT_AUTHOR = "kevin"' in content

    def test_bot_file_has_decide_function(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [
                sys.executable, "wizard.py",
                "--non-interactive",
                "--name", "DecBot",
                "--emoji", "D",
                "--style", "aggro",
                "--output-dir", str(tmp_path),
            ],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0, result.stderr
        content = (tmp_path / "decbot.py").read_text()
        assert "def decide(state):" in content


# --- Cycle 2: all 5 styles produce valid Python ---


class TestAllStylesValid:
    """Each of the 5 styles generates a file that passes ast.parse."""

    @pytest.mark.parametrize("style", PRESET_NAMES)
    def test_style_generates_parseable_bot(
        self, tmp_path: Path, style: str
    ) -> None:
        result = subprocess.run(
            [
                sys.executable, "wizard.py",
                "--non-interactive",
                "--name", f"Bot{style}",
                "--emoji", style[0].upper(),
                "--style", style,
                "--output-dir", str(tmp_path),
            ],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0, result.stderr
        content = (tmp_path / f"bot{style}.py").read_text()
        ast.parse(content)  # raises SyntaxError if invalid


# --- Cycle 3: default slider values work ---


class TestDefaultSliders:
    """Default aggression=5 and risk=5 when not specified."""

    def test_default_aggression_and_risk(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [
                sys.executable, "wizard.py",
                "--non-interactive",
                "--name", "DefaultBot",
                "--emoji", "D",
                "--style", "opportunist",
                "--output-dir", str(tmp_path),
            ],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0, result.stderr
        content = (tmp_path / "defaultbot.py").read_text()
        assert "aggression=5" in content
        assert "risk=5" in content


# --- Cycle 4: input validation errors ---


class TestInputValidation:
    """Invalid inputs cause non-zero exit code."""

    def test_invalid_style_exits_error(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [
                sys.executable, "wizard.py",
                "--non-interactive",
                "--name", "BadBot",
                "--emoji", "X",
                "--style", "sniper",
                "--output-dir", str(tmp_path),
            ],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        assert result.returncode != 0

    def test_missing_name_exits_error(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [
                sys.executable, "wizard.py",
                "--non-interactive",
                "--emoji", "X",
                "--style", "aggro",
                "--output-dir", str(tmp_path),
            ],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        assert result.returncode != 0

    def test_missing_emoji_exits_error(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [
                sys.executable, "wizard.py",
                "--non-interactive",
                "--name", "NoEmoji",
                "--style", "aggro",
                "--output-dir", str(tmp_path),
            ],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        assert result.returncode != 0

    def test_invalid_name_chars_exits_error(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [
                sys.executable, "wizard.py",
                "--non-interactive",
                "--name", "Bad@Bot!",
                "--emoji", "X",
                "--style", "aggro",
                "--output-dir", str(tmp_path),
            ],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        assert result.returncode != 0


# --- Cycle 5: name/emoji uniqueness ---


class TestNameUniqueness:
    """Duplicate BOT_NAME or BOT_EMOJI is rejected."""

    def test_duplicate_name_exits_error(self, tmp_path: Path) -> None:
        # Create first bot
        subprocess.run(
            [
                sys.executable, "wizard.py",
                "--non-interactive",
                "--name", "DupBot",
                "--emoji", "A",
                "--style", "aggro",
                "--output-dir", str(tmp_path),
            ],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        # Try to create second with same name
        result = subprocess.run(
            [
                sys.executable, "wizard.py",
                "--non-interactive",
                "--name", "DupBot",
                "--emoji", "B",
                "--style", "tank",
                "--output-dir", str(tmp_path),
            ],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        assert result.returncode != 0
        assert "already exists" in result.stderr

    def test_duplicate_emoji_exits_error(self, tmp_path: Path) -> None:
        subprocess.run(
            [
                sys.executable, "wizard.py",
                "--non-interactive",
                "--name", "BotOne",
                "--emoji", "Q",
                "--style", "aggro",
                "--output-dir", str(tmp_path),
            ],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        result = subprocess.run(
            [
                sys.executable, "wizard.py",
                "--non-interactive",
                "--name", "BotTwo",
                "--emoji", "Q",
                "--style", "tank",
                "--output-dir", str(tmp_path),
            ],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        assert result.returncode != 0
        assert "already exists" in result.stderr


# --- Cycle 6: unit tests for build_bot_source and validate_inputs ---


class TestBuildBotSourceUnit:
    """Unit tests for build_bot_source."""

    def test_contains_all_four_constants(self) -> None:
        source = build_bot_source("Foo", "F", "aggro", 5, 5, "bio", "author")
        assert "BOT_NAME = 'Foo'" in source or 'BOT_NAME = "Foo"' in source
        assert "BOT_EMOJI = 'F'" in source or 'BOT_EMOJI = "F"' in source
        assert "BOT_BIO = 'bio'" in source or 'BOT_BIO = "bio"' in source
        assert "BOT_AUTHOR = 'author'" in source or 'BOT_AUTHOR = "author"' in source

    def test_has_decide_function(self) -> None:
        source = build_bot_source("Foo", "F", "aggro", 5, 5)
        assert "def decide(state):" in source

    def test_parses_as_valid_python(self) -> None:
        source = build_bot_source("Foo", "F", "tank", 3, 7, "test", "me")
        ast.parse(source)


class TestValidateInputsUnit:
    """Unit tests for validate_inputs."""

    def test_valid_inputs_no_errors(self) -> None:
        assert validate_inputs("Bot", "B", "aggro", 5, 5) == []

    def test_empty_name_error(self) -> None:
        errors = validate_inputs("", "B", "aggro", 5, 5)
        assert any("Name" in e for e in errors)

    def test_bad_style_error(self) -> None:
        errors = validate_inputs("Bot", "B", "sniper", 5, 5)
        assert any("Style" in e for e in errors)

    def test_aggression_out_of_range(self) -> None:
        errors = validate_inputs("Bot", "B", "aggro", 0, 5)
        assert any("Aggression" in e for e in errors)

    def test_risk_out_of_range(self) -> None:
        errors = validate_inputs("Bot", "B", "aggro", 5, 11)
        assert any("Risk" in e for e in errors)
