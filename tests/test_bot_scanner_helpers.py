"""Integration tests: bot scanner + helpers/presets compatibility.

Proves that npcwars helpers imports pass AST scanning and that
generated bot code loads through the full pipeline.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from engine.bot_scanner import BLOCKED_MODULES, scan_bot_source
from engine.loader import load_bots
from npcwars.presets import PRESET_NAMES
from wizard import build_bot_source

MOCK_STATE: dict = {
    "me": {
        "x": 5, "y": 5, "hp": 100, "energy": 100,
        "attack_power": 25, "defense": 0,
        "unlocked_actions": ["attack", "defend", "move", "rest"],
        "line_budget": 50, "win_streak": 0,
    },
    "enemies": [
        {"name": "Foe", "emoji": "\U0001f47e", "x": 6, "y": 5, "hp": 80},
    ],
    "round": 1,
    "grid_size": 10,
    "storm_border": 0,
    "bumps_last_round": [],
}

HELPERS_PATH = pathlib.Path(__file__).resolve().parent.parent / "npcwars" / "helpers.py"


# --- Test 1: helpers import passes scan ---

def test_helpers_import_passes_scan() -> None:
    """A bot using 'from npcwars.helpers import ...' should have no violations."""
    source = (
        "from npcwars.helpers import Me, Enemies, Storm\n"
        "\n"
        'BOT_NAME = "TestBot"\n'
        'BOT_EMOJI = "\U0001f9ea"\n'
        "\n"
        "def decide(state):\n"
        "    me = Me(state)\n"
        "    return me.rest()\n"
    )
    violations = scan_bot_source(source)
    assert violations == []


# --- Test 2: npcwars module source has no blocked imports ---

def test_helpers_module_has_no_violations() -> None:
    """The helpers.py module itself should pass bot scanning."""
    source = HELPERS_PATH.read_text(encoding="utf-8")
    violations = scan_bot_source(source)
    assert violations == []


# --- Test 3: preset-generated bot passes scan ---

def test_preset_generated_bot_passes_scan() -> None:
    """An aggro preset wrapped in a full bot file should scan clean."""
    source = build_bot_source(
        name="AggroTest", emoji="\U0001f525", style="aggro",
        aggression=5, risk=5,
    )
    violations = scan_bot_source(source)
    assert violations == []


# --- Test 4: all 5 presets pass scan ---

@pytest.mark.parametrize("style", PRESET_NAMES)
def test_all_presets_pass_scan(style: str) -> None:
    """Every preset style should produce scanner-clean bot code."""
    source = build_bot_source(
        name=f"Test{style.title()}", emoji="\U0001f916", style=style,
        aggression=5, risk=5,
    )
    violations = scan_bot_source(source)
    assert violations == [], f"{style} preset produced violations: {violations}"


# --- Test 5: wizard-generated bot loads via load_bots() ---

def test_wizard_bot_loads_via_loader(tmp_path: pathlib.Path) -> None:
    """A wizard-generated bot file should load successfully through load_bots()."""
    source = build_bot_source(
        name="WizardBot", emoji="\U0001f9d9", style="tank",
        aggression=5, risk=5, bio="test bio", author="tester",
    )
    bot_file = tmp_path / "wizard_bot.py"
    bot_file.write_text(source, encoding="utf-8")
    bots = load_bots(str(tmp_path))
    assert len(bots) == 1
    assert bots[0]["name"] == "WizardBot"
    assert bots[0]["emoji"] == "\U0001f9d9"
    assert callable(bots[0]["decide_func"])


# --- Test 6: npcwars is NOT in BLOCKED_MODULES ---

def test_npcwars_not_blocked() -> None:
    """The npcwars package must not appear in BLOCKED_MODULES."""
    assert "npcwars" not in BLOCKED_MODULES


# --- Test 7: helpers.py has no blocked module imports (AST level) ---

def test_helpers_no_blocked_ast_imports() -> None:
    """Parse helpers.py AST and verify no import references blocked modules."""
    source = HELPERS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root not in BLOCKED_MODULES, (
                    f"helpers.py imports blocked module: {alias.name}"
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                root = node.module.split(".")[0]
                assert root not in BLOCKED_MODULES, (
                    f"helpers.py imports from blocked module: {node.module}"
                )


# --- Test 8: bot using helpers returns valid action ---

def test_helpers_bot_returns_valid_action(tmp_path: pathlib.Path) -> None:
    """A loaded helpers-based bot should return a valid action tuple."""
    source = build_bot_source(
        name="ActionBot", emoji="\U0001f3af", style="aggro",
        aggression=5, risk=5,
    )
    bot_file = tmp_path / "action_bot.py"
    bot_file.write_text(source, encoding="utf-8")
    bots = load_bots(str(tmp_path))
    assert len(bots) == 1
    result = bots[0]["decide_func"](MOCK_STATE)
    assert isinstance(result, tuple)
    assert len(result) >= 1
    valid_actions = {"attack", "defend", "move", "rest"}
    assert result[0] in valid_actions, f"Invalid action: {result[0]}"
