"""Tests for the npcwars generate CLI command (T20.6)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)


# ---------------------------------------------------------------------------
# Cycle 1: _build_prompt
# ---------------------------------------------------------------------------


class TestBuildPrompt:
    """_build_prompt loads PROMPT.md and appends extras."""

    def test_loads_prompt_md_content(self) -> None:
        from agentgrounds.wars.cli.cmd_generate import _build_prompt

        result = _build_prompt(strategy="", name="", emoji="")
        # PROMPT.md starts with this header
        assert "# NPC Wars" in result

    def test_appends_strategy(self) -> None:
        from agentgrounds.wars.cli.cmd_generate import _build_prompt

        result = _build_prompt(strategy="rush center", name="", emoji="")
        assert "Strategy: rush center" in result
        assert "## Additional Requirements" in result

    def test_appends_name_and_emoji(self) -> None:
        from agentgrounds.wars.cli.cmd_generate import _build_prompt

        result = _build_prompt(strategy="", name="Rusher", emoji="🏃")
        assert "Bot name: Rusher" in result
        assert "Bot emoji: 🏃" in result

    def test_no_extras_section_when_empty(self) -> None:
        from agentgrounds.wars.cli.cmd_generate import _build_prompt

        result = _build_prompt(strategy="", name="", emoji="")
        assert "## Additional Requirements" not in result

    def test_prompt_md_missing_exits(self, tmp_path: Path, monkeypatch: object) -> None:
        """When PROMPT.md is not found, _build_prompt exits."""
        import agentgrounds.wars.cli.cmd_generate as mod

        monkeypatch.setattr(mod, "_PROJECT_ROOT", tmp_path)  # type: ignore[attr-defined]

        with pytest.raises(SystemExit):
            mod._build_prompt(strategy="", name="", emoji="")


# ---------------------------------------------------------------------------
# Cycle 2: run (non-auto) prints prompt to stdout
# ---------------------------------------------------------------------------


def _run_cli(*args: str, timeout: float = 30) -> subprocess.CompletedProcess[str]:
    """Run ``npcwars generate`` via subprocess."""
    return subprocess.run(
        [sys.executable, "-m", "agentgrounds.wars.cli", "generate", *args],
        capture_output=True,
        text=True,
        cwd=_PROJECT_ROOT,
        timeout=timeout,
    )


class TestGenerateManual:
    """Non-auto mode prints the prompt for manual copy-paste."""

    def test_help_exits_zero(self) -> None:
        result = _run_cli("--help")
        assert result.returncode == 0
        assert "generate" in result.stdout.lower()

    def test_prints_prompt_md_content(self) -> None:
        result = _run_cli()
        assert result.returncode == 0
        assert "# NPC Wars" in result.stdout

    def test_prints_copy_paste_instructions(self) -> None:
        result = _run_cli()
        assert "Copy the above prompt" in result.stdout

    def test_strategy_appended(self) -> None:
        result = _run_cli("--strategy", "rush center")
        assert "Strategy: rush center" in result.stdout

    def test_name_and_emoji_appended(self) -> None:
        result = _run_cli("--name", "Rusher", "--emoji", "X")
        assert "Bot name: Rusher" in result.stdout
        assert "Bot emoji: X" in result.stdout


# ---------------------------------------------------------------------------
# Cycle 3: --auto error handling (no real API calls)
# ---------------------------------------------------------------------------


class TestAutoErrors:
    """--auto flag error paths without calling the real API."""

    def test_auto_without_key_exits_nonzero(self) -> None:
        env = {"PATH": "", "HOME": "/tmp"}  # no ANTHROPIC_API_KEY
        result = subprocess.run(
            [sys.executable, "-m", "agentgrounds.wars.cli", "generate", "--auto"],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
            timeout=30,
            env=env,
        )
        assert result.returncode != 0
        assert "ANTHROPIC_API_KEY" in result.stderr


# ---------------------------------------------------------------------------
# Cycle 4: CLI dispatcher integration
# ---------------------------------------------------------------------------


class TestGenerateRegistered:
    """generate subcommand is registered in the CLI dispatcher."""

    def test_generate_in_help_output(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "agentgrounds.wars.cli", "--help"],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
            timeout=30,
        )
        assert "generate" in result.stdout


class TestStripCodeFences:
    """_strip_code_fences removes markdown backtick wrappers."""

    def test_strips_python_fence(self) -> None:
        from agentgrounds.wars.cli.cmd_generate import _strip_code_fences

        raw = "```python\nprint('hi')\n```"
        assert _strip_code_fences(raw) == "print('hi')"

    def test_no_fence_passthrough(self) -> None:
        from agentgrounds.wars.cli.cmd_generate import _strip_code_fences

        raw = "print('hi')"
        assert _strip_code_fences(raw) == raw

    def test_strips_bare_fence(self) -> None:
        from agentgrounds.wars.cli.cmd_generate import _strip_code_fences

        raw = "```\ncode\n```"
        assert _strip_code_fences(raw) == "code"


class TestResolveOutputPath:
    """_resolve_output_path picks the right path from args."""

    def test_explicit_output(self) -> None:
        from agentgrounds.wars.cli.cmd_generate import _resolve_output_path
        import argparse

        ns = argparse.Namespace(output="my/bot.py", name="")
        assert _resolve_output_path(ns) == Path("my/bot.py")

    def test_name_based(self) -> None:
        from agentgrounds.wars.cli.cmd_generate import _resolve_output_path
        import argparse

        ns = argparse.Namespace(output="", name="Cool Bot")
        assert _resolve_output_path(ns) == Path("bots/cool_bot.py")

    def test_default_fallback(self) -> None:
        from agentgrounds.wars.cli.cmd_generate import _resolve_output_path
        import argparse

        ns = argparse.Namespace(output="", name="")
        assert _resolve_output_path(ns) == Path("bots/ai_generated.py")
