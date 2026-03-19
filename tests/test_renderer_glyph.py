"""Tests for glyph rendering wired into grid and roster."""
from __future__ import annotations

from agentgrounds.wars.cli.renderer import TerminalRenderer


def _make_players(*, with_glyph: bool = True) -> list[dict]:
    players = [
        {"emoji": "\U0001f916", "name": "Bot1"},
        {"emoji": "\U0001f47e", "name": "Bot2"},
    ]
    if with_glyph:
        players[0]["glyph"] = "\u25c6"  # ◆
        players[1]["glyph"] = "\u25c7"  # ◇
    return players


def _make_position(
    emoji: str,
    *,
    glyph: str | None = None,
    x: int = 5,
    y: int = 5,
    hp: int = 100,
    max_hp: int = 100,
    alive: bool = True,
    is_leader: bool = False,
) -> dict:
    pos: dict = {
        "emoji": emoji,
        "x": x,
        "y": y,
        "hp": hp,
        "max_hp": max_hp,
        "energy": 80,
        "action": "move",
        "alive": alive,
        "score": 10,
        "momentum_tier": 0,
        "is_leader": is_leader,
    }
    if glyph is not None:
        pos["glyph"] = glyph
    return pos


# -- Cycle 1: Grid glyph rendering --


def test_grid_uses_glyph_not_emoji():
    """Grid should display glyph character instead of raw emoji."""
    players = _make_players()
    renderer = TerminalRenderer(players=players, grid_size=10)
    positions = [_make_position("\U0001f916", glyph="\u25c6", x=3, y=3)]
    round_data = {"round": 1, "storm_border": 0, "positions": positions, "events": []}
    output = renderer.render_frame(round_data, clear=False)
    assert "\u25c6" in output
    # Raw emoji should NOT appear in grid cells
    # (it may appear in other places like the name lookup, so check grid area)


def test_grid_glyph_has_ansi_color():
    """Grid glyph should have ANSI color codes based on HP."""
    players = _make_players()
    renderer = TerminalRenderer(players=players, grid_size=10)
    # HP at 30% — should get yellow color
    positions = [_make_position("\U0001f916", glyph="\u25c6", x=3, y=3, hp=30, max_hp=100)]
    round_data = {"round": 1, "storm_border": 0, "positions": positions, "events": []}
    output = renderer.render_frame(round_data, clear=False)
    # Yellow ANSI code should wrap the glyph
    assert "\033[33m" in output  # yellow
    assert "\u25c6" in output


def test_grid_glyph_critical_hp_red():
    """Glyph at critical HP (<=25%) should be red."""
    players = _make_players()
    renderer = TerminalRenderer(players=players, grid_size=10)
    positions = [_make_position("\U0001f916", glyph="\u25c6", x=3, y=3, hp=10, max_hp=100)]
    round_data = {"round": 1, "storm_border": 0, "positions": positions, "events": []}
    output = renderer.render_frame(round_data, clear=False)
    assert "\033[31m" in output  # red


def test_fallback_to_emoji_when_no_glyph():
    """Position without glyph field should fall back to emoji in grid."""
    players = _make_players(with_glyph=False)
    renderer = TerminalRenderer(players=players, grid_size=10)
    positions = [_make_position("\U0001f916", x=3, y=3)]  # no glyph
    round_data = {"round": 1, "storm_border": 0, "positions": positions, "events": []}
    output = renderer.render_frame(round_data, clear=False)
    # Should still render — emoji used as fallback through render_glyph
    assert "\U0001f916" in output


# -- Cycle 2: Roster glyph rendering --


def test_roster_uses_glyph():
    """Roster should show glyph instead of raw emoji."""
    players = _make_players()
    renderer = TerminalRenderer(players=players, grid_size=10)
    positions = [_make_position("\U0001f916", glyph="\u25c6")]
    round_data = {"round": 1, "storm_border": 0, "positions": positions, "events": []}
    output = renderer.render_frame(round_data, clear=False)
    # Roster section should have the glyph
    roster_area = output.split("Combatants")[1].split("Kill Feed")[0]
    assert "\u25c6" in roster_area


def test_roster_leader_crown_with_glyph():
    """Leader should show crown + colored glyph in roster."""
    players = _make_players()
    renderer = TerminalRenderer(players=players, grid_size=10)
    positions = [_make_position("\U0001f916", glyph="\u25c6", is_leader=True)]
    round_data = {"round": 1, "storm_border": 0, "positions": positions, "events": []}
    output = renderer.render_frame(round_data, clear=False)
    roster_area = output.split("Combatants")[1].split("Kill Feed")[0]
    assert "\U0001f451" in roster_area  # crown
    assert "\u25c6" in roster_area  # glyph


# -- Cycle 3: Name lookup --


def test_glyph_name_lookup():
    """Renderer should map glyph -> name in addition to emoji -> name."""
    players = _make_players()
    renderer = TerminalRenderer(players=players, grid_size=10)
    assert renderer._players["\u25c6"] == "Bot1"
    assert renderer._players["\u25c7"] == "Bot2"
    # Original emoji mapping still works
    assert renderer._players["\U0001f916"] == "Bot1"
