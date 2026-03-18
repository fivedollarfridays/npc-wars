"""Tests for package metadata and distribution readiness."""
import tomllib
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestPackageMetadata:
    def test_pyproject_has_license(self):
        pyproject = _PROJECT_ROOT / "pyproject.toml"
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        assert "license" in data["project"]

    def test_pyproject_has_readme(self):
        pyproject = _PROJECT_ROOT / "pyproject.toml"
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        assert "readme" in data["project"]

    def test_pyproject_has_urls(self):
        pyproject = _PROJECT_ROOT / "pyproject.toml"
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        assert "urls" in data["project"]

    def test_pyproject_has_classifiers(self):
        pyproject = _PROJECT_ROOT / "pyproject.toml"
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        assert "classifiers" in data["project"]
        assert len(data["project"]["classifiers"]) >= 3

    def test_pyproject_has_keywords(self):
        pyproject = _PROJECT_ROOT / "pyproject.toml"
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        assert "keywords" in data["project"]

    def test_pyproject_has_entry_point(self):
        pyproject = _PROJECT_ROOT / "pyproject.toml"
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        assert "scripts" in data["project"]
        assert data["project"]["scripts"]["agentgrounds"] == "agentgrounds.__main__:main"

    def test_license_file_exists(self):
        assert (_PROJECT_ROOT / "LICENSE").is_file()

    def test_license_is_mit(self):
        content = (_PROJECT_ROOT / "LICENSE").read_text()
        assert "MIT" in content
