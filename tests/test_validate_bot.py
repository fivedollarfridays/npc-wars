"""Tests for scripts/validate_bot.py — syntax, attrs, sandbox, timeout."""

import subprocess
import sys

import pytest

from scripts.validate_bot import validate_bot


# --- Helpers ---


def _write_bot(tmp_path, filename, content):
    path = tmp_path / filename
    path.write_text(content)
    return str(path)


VALID_BOT = '''\
BOT_NAME = "Valid"
BOT_EMOJI = "✅"
BOT_BIO = "a fine bot"
BOT_AUTHOR = "tester"

def decide(state):
    return ("rest",)
'''

MINIMAL_BOT = '''\
BOT_NAME = "Min"
BOT_EMOJI = "⚡"

def decide(state):
    return ("move", "north")
'''


# --- Passing bots ---


class TestValidBots:
    def test_valid_bot_passes(self, tmp_path):
        path = _write_bot(tmp_path, "good.py", VALID_BOT)
        ok, errors = validate_bot(path)
        assert ok is True
        assert errors == []

    def test_minimal_bot_passes(self, tmp_path):
        path = _write_bot(tmp_path, "min.py", MINIMAL_BOT)
        ok, errors = validate_bot(path)
        assert ok is True

    def test_returns_tuple(self, tmp_path):
        path = _write_bot(tmp_path, "good.py", VALID_BOT)
        result = validate_bot(path)
        assert isinstance(result, tuple) and len(result) == 2


# --- Syntax errors ---


class TestSyntaxError:
    def test_syntax_error_fails(self, tmp_path):
        path = _write_bot(tmp_path, "bad.py", "def bad syntax(:")
        ok, errors = validate_bot(path)
        assert ok is False
        assert any("syntax" in e.lower() for e in errors)


# --- Missing required attributes ---


class TestMissingAttributes:
    def test_missing_bot_name_fails(self, tmp_path):
        path = _write_bot(tmp_path, "bad.py", '''\
BOT_EMOJI = "❌"
def decide(state): return ("rest",)
''')
        ok, errors = validate_bot(path)
        assert ok is False
        assert any("BOT_NAME" in e for e in errors)

    def test_missing_bot_emoji_fails(self, tmp_path):
        path = _write_bot(tmp_path, "bad.py", '''\
BOT_NAME = "NoEmoji"
def decide(state): return ("rest",)
''')
        ok, errors = validate_bot(path)
        assert ok is False
        assert any("BOT_EMOJI" in e for e in errors)

    def test_missing_decide_fails(self, tmp_path):
        path = _write_bot(tmp_path, "bad.py", '''\
BOT_NAME = "NoDecide"
BOT_EMOJI = "❓"
''')
        ok, errors = validate_bot(path)
        assert ok is False
        assert any("decide" in e.lower() for e in errors)

    def test_decide_not_callable_fails(self, tmp_path):
        path = _write_bot(tmp_path, "bad.py", '''\
BOT_NAME = "NotCallable"
BOT_EMOJI = "❓"
decide = "not a function"
''')
        ok, errors = validate_bot(path)
        assert ok is False
        assert any("callable" in e.lower() or "decide" in e.lower() for e in errors)


# --- Sandbox test ---


class TestSandboxValidation:
    def test_invalid_action_return_fails(self, tmp_path):
        path = _write_bot(tmp_path, "bad.py", '''\
BOT_NAME = "BadReturn"
BOT_EMOJI = "💢"
def decide(state): return "not a tuple"
''')
        ok, errors = validate_bot(path)
        assert ok is False
        assert any("action" in e.lower() or "invalid" in e.lower() for e in errors)

    def test_decide_raises_exception_fails(self, tmp_path):
        path = _write_bot(tmp_path, "bad.py", '''\
BOT_NAME = "Crasher"
BOT_EMOJI = "💥"
def decide(state): raise RuntimeError("boom")
''')
        ok, errors = validate_bot(path)
        assert ok is False

    def test_decide_timeout_fails(self, tmp_path):
        path = _write_bot(tmp_path, "slow.py", '''\
BOT_NAME = "Slow"
BOT_EMOJI = "🐢"
import time
def decide(state):
    time.sleep(10)
    return ("rest",)
''')
        ok, errors = validate_bot(path)
        assert ok is False
        assert any("timeout" in e.lower() or "time" in e.lower() for e in errors)


# --- File not found ---


class TestFileNotFound:
    def test_nonexistent_file_fails(self):
        ok, errors = validate_bot("/nonexistent/path/bot.py")
        assert ok is False
        assert any("not found" in e.lower() or "exist" in e.lower() for e in errors)


# --- CLI exit codes ---


class TestCLIExitCodes:
    def test_valid_bot_exits_zero(self, tmp_path):
        path = _write_bot(tmp_path, "good.py", VALID_BOT)
        result = subprocess.run(
            [sys.executable, "scripts/validate_bot.py", path],
            capture_output=True,
        )
        assert result.returncode == 0

    def test_invalid_bot_exits_one(self, tmp_path):
        path = _write_bot(tmp_path, "bad.py", "def bad syntax(:")
        result = subprocess.run(
            [sys.executable, "scripts/validate_bot.py", path],
            capture_output=True,
        )
        assert result.returncode == 1
