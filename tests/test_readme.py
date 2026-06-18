"""Tests for README.md content and structure."""
from __future__ import annotations

import re
from pathlib import Path

_README = Path(__file__).resolve().parent.parent / "README.md"


def _strip_leading_comment(text: str) -> str:
    """Drop a leading HTML comment block (the c5d296f FF-framing preamble)."""
    return re.sub(r"^\s*<!--.*?-->\s*", "", text, count=1, flags=re.DOTALL)


class TestReadmeStructure:
    """README has expected sections for external users."""

    def test_readme_exists(self) -> None:
        assert _README.is_file()

    def test_title(self) -> None:
        text = _strip_leading_comment(_README.read_text())
        assert text.startswith("# Agent Grounds")

    def test_has_install_section(self) -> None:
        text = _README.read_text()
        assert "## Install" in text or "pip install agent-grounds" in text

    def test_has_play_section(self) -> None:
        text = _README.read_text()
        assert "agentgrounds killswitch play" in text

    def test_has_generate_section(self) -> None:
        text = _README.read_text()
        assert "agentgrounds killswitch generate" in text

    def test_has_bot_example(self) -> None:
        text = _README.read_text()
        assert "def decide(state):" in text

    def test_no_internal_references(self) -> None:
        """README should not reference internal dev structure."""
        text = _README.read_text()
        assert "bpsai-pair" not in text
        assert ".paircoder" not in text

    def test_links_to_prompt_md(self) -> None:
        text = _README.read_text()
        assert "PROMPT.md" in text

    def test_under_150_lines(self) -> None:
        """README is a landing page, not documentation."""
        lines = _README.read_text().split("\n")
        assert len(lines) < 250, f"README is {len(lines)} lines, keep under 250"
