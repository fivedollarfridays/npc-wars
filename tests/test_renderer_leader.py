"""Tests for leader crown, drain display, and aura in renderer."""
from __future__ import annotations

from agentgrounds.wars.cli.overlay import build_aura_overlay
from agentgrounds.wars.cli.renderer import TerminalRenderer


def _make_renderer() -> TerminalRenderer:
    return TerminalRenderer(
        players=[
            {"emoji": "\U0001f916", "name": "AggroBot"},
            {"emoji": "\U0001f422", "name": "TankBot"},
            {"emoji": "\U0001f9e0", "name": "Cognify"},
        ],
        grid_size=10,
    )


def _roster_output(positions: list[dict]) -> str:
    r = _make_renderer()
    return "\n".join(r._roster(positions))


# -- Crown display ----------------------------------------------------------


def test_roster_shows_crown_for_leader() -> None:
    positions = [
        {"emoji": "\U0001f422", "x": 0, "y": 0, "hp": 100, "energy": 72,
         "alive": True, "score": 45, "momentum_tier": 3, "is_leader": True},
    ]
    output = _roster_output(positions)
    assert "\U0001f451\U0001f422" in output  # crown+turtle


def test_roster_no_crown_for_non_leader() -> None:
    positions = [
        {"emoji": "\U0001f916", "x": 0, "y": 0, "hp": 100, "energy": 95,
         "alive": True, "score": 12, "momentum_tier": 0, "is_leader": False},
    ]
    output = _roster_output(positions)
    assert "\U0001f451" not in output


def test_roster_no_crown_when_is_leader_absent() -> None:
    """Bots without is_leader key should not get crown."""
    positions = [
        {"emoji": "\U0001f916", "x": 0, "y": 0, "hp": 100, "energy": 95,
         "alive": True, "score": 12, "momentum_tier": 0},
    ]
    output = _roster_output(positions)
    assert "\U0001f451" not in output


# -- Drain display -----------------------------------------------------------


def test_roster_shows_drain_tier_2() -> None:
    positions = [
        {"emoji": "\U0001f9e0", "x": 0, "y": 0, "hp": 90, "energy": 15,
         "alive": True, "score": 28, "momentum_tier": 2, "is_leader": False},
    ]
    output = _roster_output(positions)
    assert "\u26a1-3/rd" in output


def test_roster_shows_drain_tier_3() -> None:
    positions = [
        {"emoji": "\U0001f422", "x": 0, "y": 0, "hp": 100, "energy": 72,
         "alive": True, "score": 45, "momentum_tier": 3, "is_leader": True},
    ]
    output = _roster_output(positions)
    assert "\u26a1-5/rd" in output


def test_roster_shows_drain_tier_4() -> None:
    positions = [
        {"emoji": "\U0001f422", "x": 0, "y": 0, "hp": 100, "energy": 72,
         "alive": True, "score": 80, "momentum_tier": 4, "is_leader": True},
    ]
    output = _roster_output(positions)
    assert "\u26a1-8/rd" in output


def test_roster_no_drain_tier_0() -> None:
    positions = [
        {"emoji": "\U0001f916", "x": 0, "y": 0, "hp": 100, "energy": 95,
         "alive": True, "score": 12, "momentum_tier": 0, "is_leader": False},
    ]
    output = _roster_output(positions)
    assert "/rd" not in output


def test_roster_no_drain_tier_1() -> None:
    positions = [
        {"emoji": "\U0001f916", "x": 0, "y": 0, "hp": 100, "energy": 80,
         "alive": True, "score": 20, "momentum_tier": 1, "is_leader": False},
    ]
    output = _roster_output(positions)
    assert "/rd" not in output


# -- Aura only for tier 3+ (leader) -----------------------------------------


def test_aura_only_for_tier_3_plus() -> None:
    """Only tier 3+ bots get aura dots; tier 2 does not."""
    positions = [
        {"emoji": "\U0001f916", "x": 3, "y": 3, "hp": 80, "alive": True,
         "momentum_tier": 3, "is_leader": True},
        {"emoji": "\U0001f422", "x": 7, "y": 7, "hp": 90, "alive": True,
         "momentum_tier": 2, "is_leader": False},
    ]
    overlay = build_aura_overlay(positions, grid_size=10, storm_border=0)
    # Tier-3 bot at (3,3) should have adjacent aura cells
    assert any(
        (x, y) in overlay
        for x, y in [(2, 3), (4, 3), (3, 2), (3, 4)]
    )
    # Tier-2 bot at (7,7) should NOT have adjacent aura cells
    assert not any(
        (x, y) in overlay
        for x, y in [(6, 7), (8, 7), (7, 6), (7, 8)]
    )
