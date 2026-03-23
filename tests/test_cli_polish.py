"""Tests for T20.7 — integration wiring + CLI polish."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_init_includes_starter() -> None:
    """After agentgrounds wars init, starter.py should exist in bots/."""
    from agentgrounds.wars.builtin_bots import BUILTIN_NAMES

    assert "starter" in BUILTIN_NAMES


def test_readme_mentions_play() -> None:
    """README quick start uses 'agentgrounds wars play' as primary command."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "agentgrounds wars play" in readme


def test_readme_mentions_generate() -> None:
    """README mentions the generate command."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "agentgrounds wars generate" in readme


def test_readme_mentions_prompt() -> None:
    """README references PROMPT.md."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "PROMPT.md" in readme


def test_readme_mentions_starter() -> None:
    """README mentions starter bot."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "starter" in readme.lower()


def test_readme_has_play_in_quickstart() -> None:
    """README should show play command prominently."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "agentgrounds wars play" in readme
    assert "agentgrounds wars init" in readme


def test_contributing_mentions_generate() -> None:
    """CONTRIBUTING.md mentions the generate command."""
    contrib = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "agentgrounds wars generate" in contrib


def test_contributing_mentions_prompt_md() -> None:
    """CONTRIBUTING.md references PROMPT.md."""
    contrib = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "PROMPT.md" in contrib


def test_readme_build_with_ai_section() -> None:
    """README has a bot building section."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Bot" in readme and "AI" in readme


def test_readme_learn_by_tweaking_section() -> None:
    """README has a Learn by Tweaking section."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## Learn by Tweaking" in readme
