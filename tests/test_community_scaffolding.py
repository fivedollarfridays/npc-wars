"""Tests for community scaffolding files (T14.9)."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_suggestions_template_exists():
    path = PROJECT_ROOT / "suggestions" / "TEMPLATE.md"
    assert path.exists(), "suggestions/TEMPLATE.md must exist"


def test_suggestions_template_has_category_checkboxes():
    content = (PROJECT_ROOT / "suggestions" / "TEMPLATE.md").read_text()
    assert "- [ ] New mechanic" in content
    assert "- [ ] Balance change" in content
    assert "- [ ] Quality of life" in content


def test_suggestions_template_has_priority_section():
    content = (PROJECT_ROOT / "suggestions" / "TEMPLATE.md").read_text()
    assert "## Priority Guess" in content
    assert "- [ ] Nice to have" in content


def test_showcase_readme_exists():
    path = PROJECT_ROOT / "showcase" / "README.md"
    assert path.exists(), "showcase/README.md must exist"


def test_showcase_readme_has_submission_rules():
    content = (PROJECT_ROOT / "showcase" / "README.md").read_text()
    assert "agentgrounds wars validate" in content
    assert "Max 3 bots per author" in content


def test_contributing_mentions_three_ways():
    content = (PROJECT_ROOT / "CONTRIBUTING.md").read_text()
    assert "Bot Showcase" in content
    assert "Suggestions" in content
    assert "Bug Reports" in content


def test_contributing_mentions_engine_policy():
    content = (PROJECT_ROOT / "CONTRIBUTING.md").read_text()
    assert "engine is maintained by one person" in content


def test_contributing_has_state_dict_reference():
    content = (PROJECT_ROOT / "CONTRIBUTING.md").read_text()
    assert '"me"' in content
    assert '"enemies"' in content
    assert '"storm_border"' in content


def test_contributing_has_energy_costs():
    content = (PROJECT_ROOT / "CONTRIBUTING.md").read_text()
    assert "rest" in content.lower()
    assert "15" in content  # attack cost


def test_readme_has_pip_install():
    content = (PROJECT_ROOT / "README.md").read_text()
    assert "pip install agent-grounds" in content


def test_readme_has_quick_start_commands():
    content = (PROJECT_ROOT / "README.md").read_text()
    assert "agentgrounds wars init" in content
    assert "agentgrounds wars wizard" in content
    assert "agentgrounds wars battle" in content


def test_readme_has_helpers_dsl_example():
    content = (PROJECT_ROOT / "README.md").read_text()
    assert "from agentgrounds.wars.helpers import" in content
    assert "Me(state)" in content


def test_readme_has_builtin_bots_table():
    content = (PROJECT_ROOT / "README.md").read_text()
    assert "AggroBot" in content
    assert "TankBot" in content
    assert "KiteBot" in content
    assert "ChaosBot" in content
    assert "Cognify" in content
