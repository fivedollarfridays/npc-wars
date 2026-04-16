"""Tests for package build and distribution artifacts."""

import subprocess
import tomllib
import zipfile
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestPackageBuild:
    """Verify that `python -m build` produces valid distributions."""

    def test_build_succeeds(self, tmp_path: Path) -> None:
        result = subprocess.run(
            ["python", "-m", "build", "--outdir", str(tmp_path)],
            cwd=_PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"Build failed:\n{result.stderr}"

    def test_build_produces_wheel(self, tmp_path: Path) -> None:
        subprocess.run(
            ["python", "-m", "build", "--outdir", str(tmp_path)],
            cwd=_PROJECT_ROOT,
            capture_output=True,
            timeout=120,
        )
        wheels = list(tmp_path.glob("*.whl"))
        assert len(wheels) == 1, f"Expected 1 wheel, got {len(wheels)}: {wheels}"

    def test_build_produces_sdist(self, tmp_path: Path) -> None:
        subprocess.run(
            ["python", "-m", "build", "--outdir", str(tmp_path)],
            cwd=_PROJECT_ROOT,
            capture_output=True,
            timeout=120,
        )
        sdists = list(tmp_path.glob("*.tar.gz"))
        assert len(sdists) == 1, f"Expected 1 sdist, got {len(sdists)}: {sdists}"


class TestWheelContents:
    """Verify the wheel includes required package data."""

    def _build_wheel(self, tmp_path: Path) -> Path:
        subprocess.run(
            ["python", "-m", "build", "--wheel", "--outdir", str(tmp_path)],
            cwd=_PROJECT_ROOT,
            capture_output=True,
            timeout=120,
            check=True,
        )
        wheels = list(tmp_path.glob("*.whl"))
        assert wheels, "No wheel produced"
        return wheels[0]

    def test_wheel_contains_prompt_md(self, tmp_path: Path) -> None:
        whl = self._build_wheel(tmp_path)
        with zipfile.ZipFile(whl) as zf:
            names = zf.namelist()
        prompt_files = [n for n in names if n.endswith("PROMPT.md")]
        assert prompt_files, f"PROMPT.md not in wheel. Files: {names[:20]}..."

    def test_wheel_contains_builtin_bots(self, tmp_path: Path) -> None:
        whl = self._build_wheel(tmp_path)
        with zipfile.ZipFile(whl) as zf:
            names = zf.namelist()
        bot_files = [n for n in names if "builtin_bots" in n and n.endswith(".py")]
        assert len(bot_files) >= 3, f"Expected >=3 builtin bot .py files, got {bot_files}"

    def test_wheel_contains_init(self, tmp_path: Path) -> None:
        whl = self._build_wheel(tmp_path)
        with zipfile.ZipFile(whl) as zf:
            names = zf.namelist()
        init_files = [n for n in names if n.endswith("__init__.py")]
        assert init_files, "No __init__.py found in wheel"


class TestVersionConsistency:
    """Verify version is consistent between pyproject.toml and __init__.py."""

    def test_version_matches_pyproject(self) -> None:
        with open(_PROJECT_ROOT / "pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        pyproject_version = data["project"]["version"]

        import agentgrounds
        assert agentgrounds.__version__ == pyproject_version, (
            f"__init__.py has {agentgrounds.__version__!r}, "
            f"pyproject.toml has {pyproject_version!r}"
        )


class TestPublishWorkflow:
    """Verify the publish workflow file exists and is well-formed."""

    def test_publish_workflow_exists(self) -> None:
        workflow = _PROJECT_ROOT / ".github" / "workflows" / "publish.yml"
        assert workflow.is_file(), "Missing .github/workflows/publish.yml"

    def test_publish_workflow_triggers_on_tags(self) -> None:
        import yaml  # pyyaml is in dev deps

        workflow = _PROJECT_ROOT / ".github" / "workflows" / "publish.yml"
        with open(workflow) as f:
            data = yaml.safe_load(f)
        push_config = data.get("on", data.get(True, {})).get("push", {})
        tags = push_config.get("tags", [])
        assert any("v*" in t for t in tags), f"Expected v* tag trigger, got {tags}"

    def test_publish_workflow_uses_trusted_publishing(self) -> None:
        content = (_PROJECT_ROOT / ".github" / "workflows" / "publish.yml").read_text()
        assert "pypa/gh-action-pypi-publish" in content, (
            "Workflow must use pypa/gh-action-pypi-publish"
        )

    def test_publish_workflow_has_id_token_permission(self) -> None:
        content = (_PROJECT_ROOT / ".github" / "workflows" / "publish.yml").read_text()
        assert "id-token" in content, "Workflow must have id-token permission for trusted publishing"
