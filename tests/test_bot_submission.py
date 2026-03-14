"""Tests for bot submission PR template, validation workflow, and CONTRIBUTING.md."""

import os

import yaml


TEMPLATE_PATH = ".github/PULL_REQUEST_TEMPLATE/bot_submission.md"
WORKFLOW_PATH = ".github/workflows/validate-bot.yml"
CONTRIBUTING_PATH = "CONTRIBUTING.md"


class TestPRTemplate:
    def test_template_exists(self):
        assert os.path.exists(TEMPLATE_PATH)

    def test_template_has_bot_name_field(self):
        content = open(TEMPLATE_PATH).read()
        assert "Bot Name" in content or "bot_name" in content.lower()

    def test_template_has_emoji_field(self):
        content = open(TEMPLATE_PATH).read()
        assert "Emoji" in content or "emoji" in content.lower()

    def test_template_has_checklist(self):
        content = open(TEMPLATE_PATH).read()
        assert "- [ ]" in content

    def test_template_mentions_validate_script(self):
        content = open(TEMPLATE_PATH).read()
        assert "validate_bot" in content


class TestValidateBotWorkflow:
    def _load(self):
        return yaml.safe_load(open(WORKFLOW_PATH))

    def test_workflow_exists(self):
        assert os.path.exists(WORKFLOW_PATH)

    def test_valid_yaml(self):
        assert isinstance(self._load(), dict)

    def test_triggers_on_bots_path(self):
        trigger = self._load()["on"]
        pr = trigger.get("pull_request", {})
        paths = pr.get("paths", [])
        assert any("bots" in p for p in paths)

    def test_has_validate_job(self):
        assert "validate" in self._load()["jobs"]

    def test_validate_job_runs_validate_bot_script(self):
        steps = self._load()["jobs"]["validate"]["steps"]
        commands = " ".join(s.get("run", "") for s in steps)
        assert "validate_bot.py" in commands

    def test_validate_job_skips_template(self):
        steps = self._load()["jobs"]["validate"]["steps"]
        commands = " ".join(s.get("run", "") for s in steps)
        assert "template" in commands

    def test_python_version_set(self):
        steps = self._load()["jobs"]["validate"]["steps"]
        python_steps = [s for s in steps if "setup-python" in s.get("uses", "")]
        assert len(python_steps) >= 1


class TestContributing:
    def test_contributing_exists(self):
        assert os.path.exists(CONTRIBUTING_PATH)

    def test_contributing_mentions_validate(self):
        content = open(CONTRIBUTING_PATH).read()
        assert "validate" in content

    def test_contributing_documents_state_dict(self):
        content = open(CONTRIBUTING_PATH).read()
        assert "decide" in content

    def test_contributing_documents_actions(self):
        content = open(CONTRIBUTING_PATH).read()
        assert "rest" in content and "attack" in content and "move" in content
