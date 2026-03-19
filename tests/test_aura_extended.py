"""Tests for extended aura overlay effects (leader diamond)."""
from __future__ import annotations

from agentgrounds.wars.cli.overlay import build_aura_overlay


def _pos(
    x: int = 5,
    y: int = 5,
    hp: int = 100,
    alive: bool = True,
    momentum_tier: int = 0,
    is_leader: bool = False,
    emoji: str = "A",
) -> dict:
    return {
        "emoji": emoji,
        "x": x,
        "y": y,
        "hp": hp,
        "alive": alive,
        "momentum_tier": momentum_tier,
        "is_leader": is_leader,
    }


def _diamond_cells(overlay: dict[tuple[int, int], str]) -> list[tuple[int, int]]:
    return [k for k, v in overlay.items() if "\u2666" in v]


def test_leader_gets_gold_diamond() -> None:
    positions = [_pos(x=5, y=5, is_leader=True)]
    overlay = build_aura_overlay(positions, grid_size=10, storm_border=0)
    cells = _diamond_cells(overlay)
    assert len(cells) == 1
    # Diamond should be adjacent to (5, 5)
    cell = cells[0]
    assert abs(cell[0] - 5) + abs(cell[1] - 5) == 1


def test_leader_diamond_has_yellow_color() -> None:
    positions = [_pos(x=5, y=5, is_leader=True)]
    overlay = build_aura_overlay(positions, grid_size=10, storm_border=0)
    cells = _diamond_cells(overlay)
    assert len(cells) == 1
    val = overlay[cells[0]]
    assert "\033[33m" in val  # _YELLOW


def test_non_leader_no_diamond() -> None:
    positions = [_pos(x=5, y=5, is_leader=False)]
    overlay = build_aura_overlay(positions, grid_size=10, storm_border=0)
    cells = _diamond_cells(overlay)
    assert len(cells) == 0


def test_leader_diamond_avoids_occupied() -> None:
    # Surround leader on 3 sides, diamond must go to the remaining side
    positions = [
        _pos(x=5, y=5, is_leader=True, emoji="L"),
        _pos(x=6, y=5, emoji="A"),  # right
        _pos(x=4, y=5, emoji="B"),  # left
        _pos(x=5, y=6, emoji="C"),  # down
    ]
    overlay = build_aura_overlay(positions, grid_size=10, storm_border=0)
    cells = _diamond_cells(overlay)
    assert len(cells) == 1
    assert cells[0] == (5, 4)  # only (5, 4) is free — up


def test_leader_fully_surrounded_no_diamond() -> None:
    positions = [
        _pos(x=5, y=5, is_leader=True, emoji="L"),
        _pos(x=6, y=5, emoji="A"),
        _pos(x=4, y=5, emoji="B"),
        _pos(x=5, y=6, emoji="C"),
        _pos(x=5, y=4, emoji="D"),
    ]
    overlay = build_aura_overlay(positions, grid_size=10, storm_border=0)
    cells = _diamond_cells(overlay)
    assert len(cells) == 0


def test_tier3_aura_still_works() -> None:
    positions = [_pos(x=5, y=5, momentum_tier=3)]
    overlay = build_aura_overlay(positions, grid_size=10, storm_border=0)
    # Should have yellow dots on adjacent cells, no diamonds
    assert len(overlay) > 0
    cells = _diamond_cells(overlay)
    assert len(cells) == 0
    # Check for middot character
    for v in overlay.values():
        assert "\u00b7" in v


def test_leader_plus_tier3() -> None:
    positions = [_pos(x=5, y=5, momentum_tier=3, is_leader=True)]
    overlay = build_aura_overlay(positions, grid_size=10, storm_border=0)
    # Should have both aura dots and a diamond
    cells = _diamond_cells(overlay)
    assert len(cells) >= 1
    # Should also have middot entries (tier 3 aura)
    dot_cells = [k for k, v in overlay.items() if "\u00b7" in v]
    assert len(dot_cells) >= 1


def test_dead_leader_no_diamond() -> None:
    positions = [_pos(x=5, y=5, is_leader=True, alive=False)]
    overlay = build_aura_overlay(positions, grid_size=10, storm_border=0)
    cells = _diamond_cells(overlay)
    assert len(cells) == 0
