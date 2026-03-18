"""S25 integration tests — scoring + momentum + animation pipeline."""
from __future__ import annotations

import pathlib

import pytest

from agentgrounds.wars.cli.overlay import build_aura_overlay
from agentgrounds.wars.cli.renderer import WEAPON_FX, TerminalRenderer
from engine.momentum import calculate_carryover, get_tier


# ---------------------------------------------------------------------------
# Cycle 1: unit-level assertions on FX, tiers, carryover
# ---------------------------------------------------------------------------


def test_weapon_fx_melee_is_blast():
    """WEAPON_FX['melee'] should be the blast emoji, not the old sword."""
    assert WEAPON_FX["melee"] == "\U0001f4a5"  # 💥


def test_weapon_fx_kill_has_skull_fire():
    """Kill FX should be skull + fire."""
    assert WEAPON_FX["kill"] == "\U0001f480\U0001f525"  # 💀🔥


def test_get_tier_returns_correct_tiers():
    """Verify tier boundaries: 0/10/25/40/60."""
    assert get_tier(0) == 0
    assert get_tier(9) == 0
    assert get_tier(10) == 1
    assert get_tier(24) == 1
    assert get_tier(25) == 2
    assert get_tier(39) == 2
    assert get_tier(40) == 3
    assert get_tier(59) == 3
    assert get_tier(60) == 4
    assert get_tier(100) == 4


def test_carryover_winner_80_capped():
    """Winner with 80 score: 50% = 40 (under cap)."""
    assert calculate_carryover(80, is_winner=True) == 40


def test_carryover_winner_120_capped():
    """Winner with 120 score: 50% = 60, capped at 50."""
    assert calculate_carryover(120, is_winner=True) == 50


def test_carryover_non_winner_zero():
    """Non-winner always gets 0."""
    assert calculate_carryover(80, is_winner=False) == 0


# ---------------------------------------------------------------------------
# Cycle 2: renderer — kill feed + roster
# ---------------------------------------------------------------------------

def _make_renderer(positions: list[dict] | None = None) -> TerminalRenderer:
    """Create a minimal renderer for testing."""
    players = [
        {"emoji": "\U0001f600", "name": "TestBot"},
        {"emoji": "\U0001f608", "name": "EvilBot"},
    ]
    return TerminalRenderer(players, grid_size=10)


def test_kill_feed_has_blast_emoji():
    """Hit events in the kill feed should contain the blast emoji."""
    renderer = _make_renderer()
    events = [{"type": "hit", "attacker": "\U0001f600", "target": "\U0001f608", "damage": 20}]
    round_data = {
        "round": 1, "storm_border": 0,
        "positions": [
            {"emoji": "\U0001f600", "x": 2, "y": 2, "alive": True, "hp": 80, "energy": 50, "score": 0, "momentum_tier": 0},
            {"emoji": "\U0001f608", "x": 3, "y": 2, "alive": True, "hp": 60, "energy": 50, "score": 0, "momentum_tier": 0},
        ],
        "events": events,
    }
    output = renderer.render_frame(round_data)
    assert "\U0001f4a5" in output  # 💥 in kill feed


def test_kill_feed_has_skull_fire_for_kills():
    """Kill events in the kill feed should contain skull+fire."""
    renderer = _make_renderer()
    events = [{"type": "kill", "attacker": "\U0001f600", "victim": "\U0001f608"}]
    round_data = {
        "round": 1, "storm_border": 0,
        "positions": [
            {"emoji": "\U0001f600", "x": 2, "y": 2, "alive": True, "hp": 80, "energy": 50, "score": 0, "momentum_tier": 0},
            {"emoji": "\U0001f608", "x": 3, "y": 2, "alive": False, "hp": 0, "energy": 0, "score": 0, "momentum_tier": 0},
        ],
        "events": events,
    }
    output = renderer.render_frame(round_data)
    assert "\U0001f480\U0001f525" in output  # 💀🔥


def test_roster_shows_score():
    """Roster should display '[N pts]' for each bot."""
    renderer = _make_renderer()
    round_data = {
        "round": 1, "storm_border": 0,
        "positions": [
            {"emoji": "\U0001f600", "x": 2, "y": 2, "alive": True, "hp": 80, "energy": 50, "score": 15, "momentum_tier": 0},
            {"emoji": "\U0001f608", "x": 3, "y": 2, "alive": True, "hp": 60, "energy": 50, "score": 7, "momentum_tier": 0},
        ],
        "events": [],
    }
    output = renderer.render_frame(round_data)
    assert "[15 pts]" in output
    assert "[7 pts]" in output


def test_roster_shows_tier_name():
    """Roster should show tier label for bots with momentum."""
    renderer = _make_renderer()
    round_data = {
        "round": 1, "storm_border": 0,
        "positions": [
            {"emoji": "\U0001f600", "x": 2, "y": 2, "alive": True, "hp": 80, "energy": 50, "score": 30, "momentum_tier": 2},
            {"emoji": "\U0001f608", "x": 3, "y": 2, "alive": True, "hp": 60, "energy": 50, "score": 0, "momentum_tier": 0},
        ],
        "events": [],
    }
    output = renderer.render_frame(round_data)
    assert "BATTLE FURY" in output


# ---------------------------------------------------------------------------
# Cycle 3: aura overlay
# ---------------------------------------------------------------------------

def test_aura_overlay_tier3():
    """Tier 3 bots should have aura dots on adjacent empty cells."""
    positions = [
        {"emoji": "\U0001f600", "x": 5, "y": 5, "alive": True, "momentum_tier": 3},
        {"emoji": "\U0001f608", "x": 0, "y": 0, "alive": True, "momentum_tier": 0},
    ]
    overlay = build_aura_overlay(positions, grid_size=10, storm_border=0)
    # Adjacent cells should have overlay entries
    assert (6, 5) in overlay
    assert (4, 5) in overlay
    assert (5, 6) in overlay
    assert (5, 4) in overlay
    # Bot's own cell should NOT have an overlay
    assert (5, 5) not in overlay


# ---------------------------------------------------------------------------
# Cycle 4: PROMPT.md mentions momentum
# ---------------------------------------------------------------------------

def test_prompt_md_mentions_momentum():
    """PROMPT.md should document the momentum system."""
    prompt_path = pathlib.Path(__file__).parent.parent / "PROMPT.md"
    content = prompt_path.read_text(encoding="utf-8")
    assert "Momentum" in content
    assert "score" in content
    assert "momentum_tier" in content


# ---------------------------------------------------------------------------
# Cycle 5: full match pipeline — run a real match with builtin bots
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def match_data():
    """Run one match with builtin bots and return match_data."""
    from engine.game import run_match
    from engine.loader import load_bots

    bots_dir = str(pathlib.Path(__file__).parent.parent / "agentgrounds" / "wars" / "builtin_bots")
    bot_configs = load_bots(bots_dir)
    return run_match(bot_configs, match_id=999, seed=42)


def test_match_positions_have_score(match_data: dict):
    """Every position dict in round data should have a 'score' field."""
    last_round = match_data["rounds"][-1]
    for pos in last_round["positions"]:
        assert "score" in pos, f"Missing score for {pos['emoji']}"


def test_match_positions_have_momentum_tier(match_data: dict):
    """Every position dict should have a 'momentum_tier' field."""
    last_round = match_data["rounds"][-1]
    for pos in last_round["positions"]:
        assert "momentum_tier" in pos, f"Missing momentum_tier for {pos['emoji']}"


def test_winner_has_positive_score(match_data: dict):
    """The match winner should have a positive score."""
    winner = match_data["winner"]
    assert winner != "none"
    winner_score = match_data["stats"][winner]["score"]
    assert winner_score > 0, f"Winner {winner} has score {winner_score}"


def test_match_json_has_carryover(match_data: dict):
    """Match data should contain a 'carryover' dict."""
    assert "carryover" in match_data
    assert isinstance(match_data["carryover"], dict)


def test_match_stats_have_score_and_tier(match_data: dict):
    """Stats for each bot should include score and momentum_tier."""
    for emoji, stat in match_data["stats"].items():
        assert "score" in stat, f"Missing score in stats for {emoji}"
        assert "momentum_tier" in stat, f"Missing momentum_tier in stats for {emoji}"
