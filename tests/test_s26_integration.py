"""S26 integration tests — king-of-the-hill mechanics end-to-end."""
from __future__ import annotations

import pathlib

import pytest

from agentgrounds.wars.cli.feed import format_feed_event
from agentgrounds.wars.cli.renderer import TerminalRenderer
from engine.scoring import LEADER_BOUNTY_POINTS


# ---------------------------------------------------------------------------
# Shared fixture: run one real match
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def match_data():
    """Run one match with builtin bots and return match_data."""
    from engine.game import run_match
    from engine.loader import load_bots

    bots_dir = str(
        pathlib.Path(__file__).parent.parent
        / "agentgrounds" / "wars" / "builtin_bots"
    )
    bot_configs = load_bots(bots_dir)
    return run_match(bot_configs, match_id=900, seed=42)


# ---------------------------------------------------------------------------
# Cycle 1: one-leader rule
# ---------------------------------------------------------------------------


def test_only_one_leader_per_round(match_data: dict):
    """At most 1 bot has is_leader=True in any given round."""
    for rnd in match_data["rounds"]:
        leaders = [p for p in rnd["positions"] if p.get("is_leader", False)]
        assert len(leaders) <= 1, (
            f"Round {rnd['round']}: {len(leaders)} leaders found"
        )


def test_non_leaders_capped_at_tier_2(match_data: dict):
    """Non-leader alive bots never have momentum_tier > 2."""
    for rnd in match_data["rounds"]:
        for p in rnd["positions"]:
            if not p.get("is_leader", False) and p.get("alive", False):
                assert p.get("momentum_tier", 0) <= 2, (
                    f"Round {rnd['round']}: {p['emoji']} is non-leader "
                    f"with tier {p['momentum_tier']}"
                )


def test_leader_can_reach_tier_3_plus(match_data: dict):
    """At least one round should have a leader at tier 3+."""
    found = any(
        p.get("momentum_tier", 0) >= 3
        for rnd in match_data["rounds"]
        for p in rnd["positions"]
        if p.get("is_leader", False)
    )
    assert found, "No leader ever reached tier 3+ in this match"


def test_is_leader_in_position_data(match_data: dict):
    """Every position dict must have the 'is_leader' key."""
    for rnd in match_data["rounds"]:
        for p in rnd["positions"]:
            assert "is_leader" in p, (
                f"Round {rnd['round']}: {p['emoji']} missing is_leader"
            )


# ---------------------------------------------------------------------------
# Cycle 2: energy drain
# ---------------------------------------------------------------------------


def test_energy_drain_events_exist(match_data: dict):
    """At least one momentum_drain event should exist in a multi-round match."""
    drain_events = [
        evt
        for rnd in match_data["rounds"]
        for evt in rnd.get("events", [])
        if evt.get("type") == "momentum_drain"
    ]
    assert len(drain_events) > 0, "No momentum_drain events found in match"


def test_energy_drain_has_correct_fields(match_data: dict):
    """Drain events must have emoji and energy_cost fields."""
    for rnd in match_data["rounds"]:
        for evt in rnd.get("events", []):
            if evt.get("type") == "momentum_drain":
                assert "emoji" in evt
                assert "energy_cost" in evt
                assert evt["energy_cost"] > 0


# ---------------------------------------------------------------------------
# Cycle 3: leader bounty
# ---------------------------------------------------------------------------


def test_leader_bounty_unit_level():
    """Unit test: leader_bounty scoring constant is 20."""
    assert LEADER_BOUNTY_POINTS == 20


def test_feed_contains_regicide_on_leader_bounty():
    """Format a synthetic leader_bounty event and verify REGICIDE appears."""
    evt = {
        "type": "leader_bounty",
        "killer": "\U0001f916",
        "victim": "\U0001f422",
        "bonus": 20,
    }
    line = format_feed_event(evt, 5)
    assert line is not None
    assert "REGICIDE" in line


# ---------------------------------------------------------------------------
# Cycle 4: renderer — crown + drain display
# ---------------------------------------------------------------------------


def test_roster_contains_crown(match_data: dict):
    """Rendered roster should contain crown emoji for leader."""
    renderer = TerminalRenderer(
        players=match_data.get("players", []),
        grid_size=match_data.get("grid_size", 10),
    )
    for rnd in match_data["rounds"]:
        leaders = [p for p in rnd["positions"] if p.get("is_leader")]
        if leaders:
            frame = renderer.render_frame(rnd, clear=False)
            assert "\U0001f451" in frame, "Crown emoji missing from roster"
            break
    else:
        pytest.skip("No leader found in any round")


def test_drain_rate_in_roster(match_data: dict):
    """Roster should show drain rate string for tier 2+ bots."""
    renderer = TerminalRenderer(
        players=match_data.get("players", []),
        grid_size=match_data.get("grid_size", 10),
    )
    for rnd in match_data["rounds"]:
        tier2_plus = [
            p for p in rnd["positions"]
            if p.get("alive") and p.get("momentum_tier", 0) >= 2
        ]
        if tier2_plus:
            frame = renderer.render_frame(rnd, clear=False)
            # e.g. "⚡-3/rd"
            assert "/rd" in frame, "Drain rate string missing from roster"
            break
    else:
        pytest.skip("No tier 2+ bot found in any round")


# ---------------------------------------------------------------------------
# Cycle 5: PROMPT.md content
# ---------------------------------------------------------------------------


def test_prompt_md_mentions_leader():
    """PROMPT.md should mention leader mechanics."""
    prompt_path = pathlib.Path(__file__).parent.parent / "PROMPT.md"
    content = prompt_path.read_text(encoding="utf-8")
    assert "leader" in content.lower()
    assert "bounty" in content.lower()


def test_prompt_md_mentions_king_of_the_hill():
    """PROMPT.md should have a King of the Hill section."""
    prompt_path = pathlib.Path(__file__).parent.parent / "PROMPT.md"
    content = prompt_path.read_text(encoding="utf-8")
    assert "King of the Hill" in content


def test_prompt_md_mentions_is_leader_field():
    """PROMPT.md should document the is_leader state field."""
    prompt_path = pathlib.Path(__file__).parent.parent / "PROMPT.md"
    content = prompt_path.read_text(encoding="utf-8")
    assert "is_leader" in content


# ---------------------------------------------------------------------------
# Cycle 6: importability of public API
# ---------------------------------------------------------------------------


def test_no_dead_public_functions():
    """All new S26 public functions and constants are importable."""
    from engine.momentum import (  # noqa: F401
        TIER_ENERGY_DRAIN,
        apply_energy_drain,
        determine_leader,
    )
    from engine.scoring import LEADER_BOUNTY_POINTS  # noqa: F401

    assert callable(determine_leader)
    assert callable(apply_energy_drain)
    assert isinstance(TIER_ENERGY_DRAIN, dict)
    assert isinstance(LEADER_BOUNTY_POINTS, int)
