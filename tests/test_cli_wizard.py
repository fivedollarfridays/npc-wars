"""Tests for the CLI wizard subcommand (T14.5)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run ``python -m npcwars.cli`` with given args."""
    return subprocess.run(
        [sys.executable, "-m", "npcwars.cli", *args],
        capture_output=True,
        text=True,
        cwd=cwd or _PROJECT_ROOT,
        timeout=30,
    )


class TestWizardHelp:
    """Wizard --help works through CLI dispatcher."""

    def test_wizard_help_exits_zero(self) -> None:
        result = _run_cli("wizard", "--help")
        assert result.returncode == 0

    def test_wizard_help_mentions_non_interactive(self) -> None:
        result = _run_cli("wizard", "--help")
        assert "--non-interactive" in result.stdout


class TestWizardNonInteractive:
    """Non-interactive wizard creates valid bot files."""

    def test_creates_bot_file(self, tmp_path: Path) -> None:
        result = _run_cli(
            "wizard", "--non-interactive",
            "--name", "TestBot",
            "--emoji", "T",
            "--style", "aggro",
            "--output-dir", str(tmp_path),
        )
        assert result.returncode == 0
        assert (tmp_path / "testbot.py").exists()

    def test_bot_file_contains_bot_name(self, tmp_path: Path) -> None:
        _run_cli(
            "wizard", "--non-interactive",
            "--name", "TestBot",
            "--emoji", "T",
            "--style", "aggro",
            "--output-dir", str(tmp_path),
        )
        content = (tmp_path / "testbot.py").read_text()
        assert "BOT_NAME" in content

    def test_bot_file_contains_decide(self, tmp_path: Path) -> None:
        _run_cli(
            "wizard", "--non-interactive",
            "--name", "TestBot",
            "--emoji", "T",
            "--style", "aggro",
            "--output-dir", str(tmp_path),
        )
        content = (tmp_path / "testbot.py").read_text()
        assert "def decide" in content

    def test_output_dir_created_if_missing(self, tmp_path: Path) -> None:
        out_dir = tmp_path / "nested" / "bots"
        result = _run_cli(
            "wizard", "--non-interactive",
            "--name", "TestBot",
            "--emoji", "T",
            "--style", "tank",
            "--output-dir", str(out_dir),
        )
        assert result.returncode == 0
        assert (out_dir / "testbot.py").exists()


class TestWizardErrors:
    """Error cases return non-zero exit codes."""

    def test_invalid_style_exits_nonzero(self, tmp_path: Path) -> None:
        result = _run_cli(
            "wizard", "--non-interactive",
            "--name", "TestBot",
            "--emoji", "T",
            "--style", "invalid_style",
            "--output-dir", str(tmp_path),
        )
        assert result.returncode != 0

    def test_missing_name_exits_nonzero(self, tmp_path: Path) -> None:
        result = _run_cli(
            "wizard", "--non-interactive",
            "--emoji", "T",
            "--style", "aggro",
            "--output-dir", str(tmp_path),
        )
        assert result.returncode != 0
