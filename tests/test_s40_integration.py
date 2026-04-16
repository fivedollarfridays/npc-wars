"""S40 Integration Gate — install flow end-to-end validation."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class TestPackageInstall:
    def test_version_importable(self) -> None:
        from agentgrounds import __version__
        assert __version__ == "0.2.0"

    def test_version_cli(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "agentgrounds", "--version"],
            capture_output=True, text=True,
        )
        assert "0.2.0" in result.stdout or "0.2.0" in result.stderr

    def test_wars_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "agentgrounds", "wars", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "play" in result.stdout
        assert "generate" in result.stdout
        assert "init" in result.stdout

    def test_helpers_importable(self) -> None:
        from agentgrounds.wars.helpers import Me, Enemies, Storm
        assert Me is not None
        assert Enemies is not None
        assert Storm is not None


class TestGenerateCommand:
    def test_generate_produces_prompt(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "agentgrounds", "wars", "generate",
             "--strategy", "test", "--name", "TestBot", "--emoji", "🤖"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "decide(state)" in result.stdout
        assert "TestBot" in result.stdout

    def test_generate_no_pip_install_in_output(self) -> None:
        """Generate output should not confuse AI with installation instructions."""
        result = subprocess.run(
            [sys.executable, "-m", "agentgrounds", "wars", "generate",
             "--strategy", "test"],
            capture_output=True, text=True,
        )
        # The AI-facing prompt should not contain pip install instructions
        assert "pip install" not in result.stdout


class TestPromptMdBundled:
    def test_prompt_in_package_data(self) -> None:
        """PROMPT.md is accessible from installed package."""
        prompt_path = Path(__file__).resolve().parent.parent / "agentgrounds" / "wars" / "data" / "PROMPT.md"
        assert prompt_path.exists(), f"PROMPT.md not found at {prompt_path}"
        content = prompt_path.read_text()
        assert "decide(state)" in content

    def test_prompt_under_3000_words(self) -> None:
        prompt_path = Path(__file__).resolve().parent.parent / "agentgrounds" / "wars" / "data" / "PROMPT.md"
        words = len(prompt_path.read_text().split())
        assert words < 3000, f"PROMPT.md: {words} words"


class TestBuildArtifacts:
    def test_build_succeeds(self) -> None:
        """python -m build produces distribution files."""
        result = subprocess.run(
            [sys.executable, "-m", "build"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).resolve().parent.parent),
        )
        # Build may not have 'build' installed — skip if so
        if "No module named build" in result.stderr:
            import pytest
            pytest.skip("build module not installed")
        assert result.returncode == 0

    def test_publish_workflow_exists(self) -> None:
        workflow = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "publish.yml"
        assert workflow.exists()
        content = workflow.read_text()
        assert "pypi" in content.lower() or "PyPI" in content
