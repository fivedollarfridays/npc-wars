"""T56.6: CI security audit, pre-commit config, and clean stashes."""

from pathlib import Path

import yaml


class TestCISecurityAudit:
    """CI workflow includes pip-audit security scanning."""

    def test_ci_has_pip_audit(self) -> None:
        ci = Path(".github/workflows/ci.yml").read_text()
        assert "pip-audit" in ci

    def test_ci_audit_is_advisory(self) -> None:
        """Security audit should not block CI (uses || true)."""
        ci = Path(".github/workflows/ci.yml").read_text()
        assert "pip-audit" in ci
        assert "|| true" in ci


class TestPreCommitConfig:
    """Pre-commit configuration for code quality hooks."""

    def test_precommit_config_exists(self) -> None:
        assert Path(".pre-commit-config.yaml").exists()

    def test_precommit_valid_yaml(self) -> None:
        content = Path(".pre-commit-config.yaml").read_text()
        data = yaml.safe_load(content)
        assert "repos" in data

    def test_precommit_has_ruff(self) -> None:
        content = Path(".pre-commit-config.yaml").read_text()
        assert "ruff" in content

    def test_precommit_has_trailing_whitespace(self) -> None:
        content = Path(".pre-commit-config.yaml").read_text()
        assert "trailing-whitespace" in content

    def test_precommit_has_end_of_file_fixer(self) -> None:
        content = Path(".pre-commit-config.yaml").read_text()
        assert "end-of-file-fixer" in content

    def test_precommit_has_large_file_check(self) -> None:
        content = Path(".pre-commit-config.yaml").read_text()
        assert "check-added-large-files" in content
