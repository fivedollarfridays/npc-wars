"""Tests for open-source documentation — T66.3."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestReadme:
    """README.md must have key sections for open-source on-ramp."""

    def _readme(self) -> str:
        return (ROOT / "README.md").read_text()

    def test_exists(self):
        assert (ROOT / "README.md").exists()

    def test_three_command_demo(self):
        """README shows a 3-command demo (install, init, play)."""
        text = self._readme()
        assert "pip install agent-grounds" in text
        assert "agentgrounds killswitch init" in text or "agentgrounds wars init" in text
        assert "agentgrounds killswitch play" in text or "agentgrounds wars play" in text

    def test_feature_list(self):
        text = self._readme()
        assert "feature" in text.lower() or "## what" in text.lower() or "## game" in text.lower()

    def test_architecture_overview(self):
        text = self._readme()
        assert "architecture" in text.lower() or "how it works" in text.lower()

    def test_both_games_mentioned(self):
        text = self._readme()
        assert "Kill Switch" in text or "killswitch" in text.lower()
        assert "Code Circuit" in text or "circuit" in text.lower()

    def test_getting_started_link(self):
        text = self._readme()
        assert "getting-started" in text.lower() or "getting started" in text.lower()

    def test_license_mentioned(self):
        text = self._readme()
        assert "MIT" in text

    def test_no_broken_markdown_links(self):
        """All [text](path) links to local files should point to existing files."""
        text = self._readme()
        links = re.findall(r"\[.*?\]\(([^http].*?)\)", text)
        for link in links:
            # Strip anchors
            path = link.split("#")[0]
            if path:
                assert (ROOT / path).exists(), f"Broken link: {path}"


class TestGettingStarted:
    """Getting Started guide must exist and cover the full on-ramp."""

    def _guide(self) -> str:
        return (ROOT / "docs" / "getting-started.md").read_text()

    def test_exists(self):
        assert (ROOT / "docs" / "getting-started.md").exists()

    def test_pip_install(self):
        assert "pip install" in self._guide()

    def test_init_command(self):
        text = self._guide()
        assert "init" in text

    def test_play_command(self):
        text = self._guide()
        assert "play" in text

    def test_episode_section(self):
        text = self._guide()
        assert "episode" in text.lower() or "watch" in text.lower() or "replay" in text.lower()


class TestPromptMd:
    """PROMPT.md per game reviewed and polished."""

    def test_killswitch_prompt_exists(self):
        assert (ROOT / "PROMPT.md").exists()

    def test_killswitch_prompt_has_bot_format(self):
        text = (ROOT / "PROMPT.md").read_text()
        assert "BOT_NAME" in text
        assert "decide(state)" in text

    def test_killswitch_prompt_has_equipment(self):
        text = (ROOT / "PROMPT.md").read_text()
        assert "Equipment" in text

    def test_killswitch_prompt_packaged(self):
        """PROMPT.md is also packaged in agentgrounds.wars.data."""
        assert (ROOT / "agentgrounds" / "wars" / "data" / "PROMPT.md").exists()


class TestContributing:
    """CONTRIBUTING.md must cover commentary templates, effects, new games."""

    def _contrib(self) -> str:
        return (ROOT / "CONTRIBUTING.md").read_text()

    def test_exists(self):
        assert (ROOT / "CONTRIBUTING.md").exists()

    def test_commentary_section(self):
        text = self._contrib()
        assert "commentary" in text.lower()

    def test_effects_section(self):
        text = self._contrib()
        assert "effect" in text.lower() or "spectacle" in text.lower()

    def test_new_games_section(self):
        text = self._contrib()
        assert "new game" in text.lower() or "add a game" in text.lower()

    def test_bot_submission(self):
        text = self._contrib()
        assert "showcase" in text.lower() or "bot" in text.lower()


class TestLicense:
    """LICENSE file must exist with MIT terms."""

    def test_exists(self):
        assert (ROOT / "LICENSE").exists()

    def test_mit(self):
        text = (ROOT / "LICENSE").read_text()
        assert "MIT" in text

    def test_copyright(self):
        text = (ROOT / "LICENSE").read_text()
        assert "Copyright" in text


class TestDocsRender:
    """All docs should use valid markdown that renders on GitHub."""

    def test_no_raw_html_in_readme(self):
        text = (ROOT / "README.md").read_text()
        # Allow img tags for screenshots but no script tags
        assert "<script" not in text

    def test_readme_starts_with_heading(self):
        text = (ROOT / "README.md").read_text()
        assert text.strip().startswith("#")

    def test_contributing_starts_with_heading(self):
        text = (ROOT / "CONTRIBUTING.md").read_text()
        assert text.strip().startswith("#")

    def test_getting_started_starts_with_heading(self):
        text = (ROOT / "docs" / "getting-started.md").read_text()
        assert text.strip().startswith("#")
