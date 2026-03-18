"""Tests for PROMPT.md — the agent arena prompt document."""

from __future__ import annotations

from pathlib import Path

PROMPT_PATH = Path(__file__).resolve().parent.parent / "PROMPT.md"


def _read_prompt() -> str:
    assert PROMPT_PATH.exists(), f"PROMPT.md not found at {PROMPT_PATH}"
    return PROMPT_PATH.read_text(encoding="utf-8")


def test_prompt_md_exists() -> None:
    assert PROMPT_PATH.exists(), "PROMPT.md must exist at the project root"


def test_prompt_contains_state_dict() -> None:
    text = _read_prompt()
    # Must document the state dict keys that decide() receives
    for key in ("me", "enemies", "grid_size", "storm_border", "round"):
        assert key in text, f"PROMPT.md must document state key '{key}'"
    # Must document the 'me' sub-keys
    for field in ("hp", "energy", "attack_power"):
        assert field in text, f"PROMPT.md must document me.{field}"


def test_prompt_contains_actions() -> None:
    text = _read_prompt()
    for action in ("move", "attack", "defend", "rest"):
        assert action in text, f"PROMPT.md must document the '{action}' action"


def test_prompt_contains_decide_function() -> None:
    text = _read_prompt()
    assert "def decide(state)" in text, (
        "PROMPT.md must contain the decide(state) function signature"
    )


def test_prompt_contains_bot_format() -> None:
    text = _read_prompt()
    assert "BOT_NAME" in text, "PROMPT.md must document BOT_NAME"
    assert "BOT_EMOJI" in text, "PROMPT.md must document BOT_EMOJI"


def test_prompt_under_word_limit() -> None:
    text = _read_prompt()
    word_count = len(text.split())
    assert word_count < 3000, (
        f"PROMPT.md is {word_count} words — must be under 3000"
    )


def test_prompt_contains_helpers_api() -> None:
    text = _read_prompt()
    # Must mention the three helper classes
    for cls in ("Me", "Enemies", "Storm"):
        assert cls in text, f"PROMPT.md must mention the {cls} helper class"
    # Must mention importing from agentgrounds.wars.helpers
    assert "agentgrounds.wars.helpers" in text, (
        "PROMPT.md must show how to import helpers from agentgrounds.wars.helpers"
    )
