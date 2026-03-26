"""Tests for Sprint 50 bot scanner blocklist expansion."""

import pytest

from engine.bot_scanner import scan_bot_source

NEW_BLOCKED = [
    "ftplib", "smtplib", "telnetlib", "pty", "tty",
    "tempfile", "zipfile", "xmlrpc",
]


@pytest.mark.parametrize("module", NEW_BLOCKED)
def test_import_blocked(module: str) -> None:
    """Direct import of new blocked module is rejected."""
    source = (
        f"import {module}\n"
        "BOT_NAME='x'\nBOT_EMOJI='x'\n"
        "def decide(state): return ('rest',)"
    )
    errors = scan_bot_source(source)
    assert any(module in e for e in errors)


@pytest.mark.parametrize("module", NEW_BLOCKED)
def test_from_import_blocked(module: str) -> None:
    """From-import of new blocked module is rejected."""
    source = (
        f"from {module} import something\n"
        "BOT_NAME='x'\nBOT_EMOJI='x'\n"
        "def decide(state): return ('rest',)"
    )
    errors = scan_bot_source(source)
    assert any(module in e for e in errors)


def test_existing_blocked_still_blocked() -> None:
    """Existing blocked modules are still blocked (regression check)."""
    for module in ["os", "subprocess", "socket", "sys"]:
        source = (
            f"import {module}\n"
            "BOT_NAME='x'\nBOT_EMOJI='x'\n"
            "def decide(state): return ('rest',)"
        )
        errors = scan_bot_source(source)
        assert errors, f"{module} should be blocked"


def test_allowed_modules_still_pass() -> None:
    """Safe modules like math and random are still allowed."""
    source = (
        "import math\nimport random\n"
        "BOT_NAME='x'\nBOT_EMOJI='x'\n"
        "def decide(state): return ('rest',)"
    )
    errors = scan_bot_source(source)
    assert not errors
