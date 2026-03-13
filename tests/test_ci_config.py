"""Structural tests for .github/workflows/ci.yml."""

import yaml


CI_PATH = ".github/workflows/ci.yml"


def _load():
    with open(CI_PATH) as f:
        return yaml.safe_load(f)


class TestCIYaml:
    def test_valid_yaml(self):
        data = _load()
        assert isinstance(data, dict)

    def test_triggers_on_push_and_pr(self):
        triggers = _load()["on"]
        assert "push" in triggers
        assert "pull_request" in triggers

    def test_push_includes_main(self):
        push = _load()["on"]["push"]
        assert "main" in push["branches"]

    def test_has_lint_job(self):
        assert "lint" in _load()["jobs"]

    def test_has_test_job(self):
        assert "test" in _load()["jobs"]

    def test_lint_job_runs_ruff(self):
        steps = _load()["jobs"]["lint"]["steps"]
        commands = " ".join(s.get("run", "") for s in steps)
        assert "ruff" in commands

    def test_test_job_runs_pytest_with_coverage(self):
        steps = _load()["jobs"]["test"]["steps"]
        commands = " ".join(s.get("run", "") for s in steps)
        assert "pytest" in commands
        assert "--cov" in commands

    def test_coverage_gate_step_exists(self):
        steps = _load()["jobs"]["test"]["steps"]
        commands = " ".join(s.get("run", "") for s in steps)
        assert "fail-under" in commands or "coverage" in commands

    def test_coverage_artifact_uploaded(self):
        steps = _load()["jobs"]["test"]["steps"]
        artifact_steps = [s for s in steps if "upload-artifact" in s.get("uses", "")]
        assert len(artifact_steps) >= 1

    def test_validate_bots_job_exists(self):
        assert "validate-bots" in _load()["jobs"]

    def test_python_version_specified(self):
        test_steps = _load()["jobs"]["test"]["steps"]
        python_steps = [s for s in test_steps if "setup-python" in s.get("uses", "")]
        assert len(python_steps) >= 1
        version = python_steps[0]["with"]["python-version"]
        assert version.startswith("3.")
