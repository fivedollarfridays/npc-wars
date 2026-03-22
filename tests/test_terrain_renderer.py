"""Tests for terrain rendering in TerminalRenderer grid."""
from __future__ import annotations

from agentgrounds.wars.cli.renderer import TerminalRenderer

# ANSI color codes used by terrain rendering
_RST = "\033[0m"
_DIM = "\033[2m"
_GRAY = "\033[90m"
_BLUE = "\033[34m"
_YELLOW = "\033[33m"
_GREEN = "\033[32m"
_PURPLE = "\033[35m"


def _make_terrain_tiles(grid_size: int, default: str = "open") -> list[list[str]]:
    """Create a grid_size x grid_size tile grid."""
    return [[default] * grid_size for _ in range(grid_size)]


def _make_renderer(
    grid_size: int = 10,
    terrain_tiles: list[list[str]] | None = None,
) -> TerminalRenderer:
    """Create a renderer with optional terrain tiles."""
    players = [{"emoji": "\U0001f916", "name": "Bot"}]
    r = TerminalRenderer(players, grid_size)
    if terrain_tiles is not None:
        r.set_terrain(terrain_tiles)
    return r


def test_renderer_accepts_terrain() -> None:
    """Renderer should accept terrain tiles via set_terrain."""
    tiles = _make_terrain_tiles(10)
    r = _make_renderer(10, terrain_tiles=tiles)
    assert r._terrain_tiles is not None


def test_grid_shows_wall_char() -> None:
    """Wall tiles should render as # with gray color, not empty char."""
    tiles = _make_terrain_tiles(10)
    tiles[3][4] = "wall"  # y=3, x=4
    r = _make_renderer(10, terrain_tiles=tiles)
    positions = [{"emoji": "\U0001f916", "glyph": "\U0001f916", "x": 0, "y": 0,
                  "hp": 100, "max_hp": 100, "alive": True}]
    lines = r._grid(positions, storm=0)
    # The grid row for y=3 should contain the wall character
    row_line = lines[4]  # +1 for top border
    assert " #" in row_line or f"{_GRAY} #" in row_line


def test_grid_shows_water_char() -> None:
    """Water tiles should render as ~ with blue color."""
    tiles = _make_terrain_tiles(10)
    tiles[5][6] = "water"
    r = _make_renderer(10, terrain_tiles=tiles)
    positions = [{"emoji": "\U0001f916", "glyph": "\U0001f916", "x": 0, "y": 0,
                  "hp": 100, "max_hp": 100, "alive": True}]
    lines = r._grid(positions, storm=0)
    row_line = lines[6]  # y=5, +1 for border
    assert " ~" in row_line or f"{_BLUE} ~" in row_line


def test_grid_shows_crystal_char() -> None:
    """Crystal tiles should render as * with magenta color."""
    tiles = _make_terrain_tiles(10)
    tiles[1][1] = "crystal"
    r = _make_renderer(10, terrain_tiles=tiles)
    positions = [{"emoji": "\U0001f916", "glyph": "\U0001f916", "x": 0, "y": 0,
                  "hp": 100, "max_hp": 100, "alive": True}]
    lines = r._grid(positions, storm=0)
    row_line = lines[2]  # y=1, +1 for border
    assert " *" in row_line or f"{_PURPLE} *" in row_line


def test_open_tiles_show_empty_char() -> None:
    """Open tiles should still show the normal empty char."""
    tiles = _make_terrain_tiles(10)
    r = _make_renderer(10, terrain_tiles=tiles)
    positions: list[dict] = []
    lines = r._grid(positions, storm=0)
    # All interior cells should be the standard empty char
    row_line = lines[1]  # first row after border
    assert "\u00b7" in row_line


def test_bot_renders_over_terrain() -> None:
    """Bot glyphs should render on top of terrain tiles."""
    tiles = _make_terrain_tiles(10)
    tiles[3][4] = "wall"
    r = _make_renderer(10, terrain_tiles=tiles)
    # Bot on the wall tile
    positions = [{"emoji": "\U0001f916", "glyph": "\U0001f916", "x": 4, "y": 3,
                  "hp": 100, "max_hp": 100, "alive": True}]
    lines = r._grid(positions, storm=0)
    row_line = lines[4]  # y=3, +1 for border
    # The bot glyph should be present, not the wall char
    assert "\U0001f916" in row_line


def test_no_terrain_defaults_to_empty() -> None:
    """Without terrain, all cells show normal empty char."""
    r = _make_renderer(10, terrain_tiles=None)
    positions: list[dict] = []
    lines = r._grid(positions, storm=0)
    row_line = lines[1]
    # Should have the default empty char
    assert "\u00b7" in row_line
    # Should NOT have terrain chars
    assert " #" not in row_line
    assert " ~" not in row_line
