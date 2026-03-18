"""Integration tests for the Vibe Wizard pipeline.

Proves that wizard-generated bots, preset bots, and the example_vibes bot
all work end-to-end in real matches via the engine.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from engine.game import run_match
from engine.loader import load_bots
from agentgrounds.wars.presets import PRESET_NAMES
from scripts.validate_bot import validate_bot
from wizard import build_bot_source


_DUMMY_BOT_SOURCE = '''\
BOT_NAME = "Dummy"
BOT_EMOJI = "\\U0001f3af"

def decide(state):
    return ("rest",)
'''


def _write_bot(tmp_path: Path, filename: str, source: str) -> Path:
    """Write a bot source file into a bots subdirectory under tmp_path."""
    bots_dir = tmp_path / "bots"
    bots_dir.mkdir(exist_ok=True)
    bot_file = bots_dir / filename
    bot_file.write_text(source)
    return bot_file


def _load_and_run(bots_dir: Path, seed: int = 42) -> dict:
    """Load bots from directory and run a match. Returns match_data."""
    configs = load_bots(str(bots_dir))
    assert len(configs) >= 2, f"Need at least 2 bots, got {len(configs)}"
    return run_match(configs, seed=seed)


# -- Test 1: Wizard-generated bot completes a match --


def test_wizard_bot_completes_match(tmp_path: Path) -> None:
    """A bot generated via build_bot_source loads and finishes a real match."""
    source = build_bot_source(
        name="TestWiz", emoji="\U0001f9d9", style="aggro",
        aggression=5, risk=5,
    )
    _write_bot(tmp_path, "test_wiz.py", source)
    _write_bot(tmp_path, "dummy.py", _DUMMY_BOT_SOURCE)

    match_data = _load_and_run(tmp_path / "bots")

    bot_emojis = {p["emoji"] for p in match_data["players"]}
    assert "\U0001f9d9" in bot_emojis
    stats = match_data["stats"]
    assert "\U0001f9d9" in stats
    assert stats["\U0001f9d9"]["rounds_survived"] > 0


# -- Test 2: All 5 presets complete matches (parametrized) --


@pytest.mark.parametrize("style", PRESET_NAMES)
def test_preset_bot_in_match(style: str, tmp_path: Path) -> None:
    """Each preset style generates a bot that runs in a match without errors."""
    source = build_bot_source(
        name=f"Preset_{style}", emoji="\U0001f916",
        style=style, aggression=5, risk=5,
    )
    _write_bot(tmp_path, "preset_bot.py", source)
    _write_bot(tmp_path, "dummy.py", _DUMMY_BOT_SOURCE)

    match_data = _load_and_run(tmp_path / "bots")

    assert "\U0001f916" in match_data["stats"]
    assert match_data["stats"]["\U0001f916"]["rounds_survived"] > 0


# -- Test 3: example_vibes.py works in a match --


def test_example_vibes_in_match(tmp_path: Path) -> None:
    """The real bots/example_vibes.py bot participates in a match."""
    src = Path(__file__).resolve().parent.parent / "bots" / "example_vibes.py"
    assert src.exists(), f"example_vibes.py not found at {src}"

    bots_dir = tmp_path / "bots"
    bots_dir.mkdir()
    shutil.copy(src, bots_dir / "example_vibes.py")
    _write_bot(tmp_path, "dummy.py", _DUMMY_BOT_SOURCE)

    match_data = _load_and_run(bots_dir)

    # Cognify bot uses brain emoji
    assert "\U0001f9e0" in match_data["stats"]
    assert match_data["stats"]["\U0001f9e0"]["rounds_survived"] > 0


# -- Test 4: Helpers-based bot makes non-trivial decisions --


def test_helpers_bot_nontrivial_actions(tmp_path: Path) -> None:
    """A helpers-based bot does not just rest every round."""
    source = build_bot_source(
        name="ActiveBot", emoji="\U0001f525", style="aggro",
        aggression=8, risk=8,
    )
    _write_bot(tmp_path, "active_bot.py", source)
    _write_bot(tmp_path, "dummy.py", _DUMMY_BOT_SOURCE)

    match_data = _load_and_run(tmp_path / "bots")
    rounds = match_data["rounds"]

    # Collect all actions for ActiveBot across rounds (stored in positions list)
    non_rest_count = 0
    for rnd in rounds:
        for pos in rnd.get("positions", []):
            if pos["emoji"] == "\U0001f525":
                action = pos.get("action", "rest")
                if not action.startswith("rest"):
                    non_rest_count += 1

    assert non_rest_count > 0, "Helpers bot should do more than just rest"


# -- Test 5: Generated bot coexists with existing bots --


def test_wizard_bot_coexists_with_existing(tmp_path: Path) -> None:
    """A wizard bot and an existing example bot both appear in match stats."""
    # Copy example_vibes
    src = Path(__file__).resolve().parent.parent / "bots" / "example_vibes.py"
    bots_dir = tmp_path / "bots"
    bots_dir.mkdir()
    shutil.copy(src, bots_dir / "example_vibes.py")

    # Generate a wizard bot
    source = build_bot_source(
        name="WizCoexist", emoji="\U0001f308", style="tank",
        aggression=5, risk=5,
    )
    (bots_dir / "wiz_coexist.py").write_text(source)

    match_data = _load_and_run(bots_dir)

    stats = match_data["stats"]
    assert "\U0001f9e0" in stats, "Cognify should be in stats"
    assert "\U0001f308" in stats, "WizCoexist should be in stats"


# -- Test 6: Full pipeline smoke test --


def test_full_pipeline_smoke(tmp_path: Path) -> None:
    """Complete user journey: generate, write, validate, load, run, check."""
    # 1. Generate bot source via wizard
    source = build_bot_source(
        name="SmokeTester", emoji="\U0001f4a8", style="opportunist",
        aggression=7, risk=3, bio="smoke test bot", author="test",
    )

    # 2. Write to file
    bots_dir = tmp_path / "bots"
    bots_dir.mkdir()
    bot_path = bots_dir / "smoke_tester.py"
    bot_path.write_text(source)

    # 3. Validate via validate_bot
    ok, errors = validate_bot(str(bot_path))
    assert ok, f"validate_bot failed: {errors}"

    # 4. Write opponent
    _write_bot(tmp_path, "dummy.py", _DUMMY_BOT_SOURCE)

    # 5. Load via load_bots and run match
    configs = load_bots(str(bots_dir))
    assert len(configs) >= 2

    match_data = run_match(configs, seed=42)

    # 6. Check stats
    assert "\U0001f4a8" in match_data["stats"]
    assert match_data["stats"]["\U0001f4a8"]["rounds_survived"] > 0
    assert match_data["winner"] != "none"
    assert len(match_data["rounds"]) > 0
