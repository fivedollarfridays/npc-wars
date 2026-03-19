"""Tests for HP-dependent glyph foreground coloring and stat backgrounds."""
from __future__ import annotations

from agentgrounds.wars.cli.glyph_render import get_primary_stat, render_glyph

_RST = "\033[0m"
_BRIGHT_WHITE = "\033[97m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"


def test_full_hp_bright_white() -> None:
    result = render_glyph("\u25c6", 100, 100)
    assert _BRIGHT_WHITE in result


def test_high_hp_green() -> None:
    result = render_glyph("\u25c6", 70, 100)
    assert _GREEN in result


def test_medium_hp_yellow() -> None:
    result = render_glyph("\u25c6", 40, 100)
    assert _YELLOW in result


def test_low_hp_red() -> None:
    result = render_glyph("\u25c6", 20, 100)
    assert _RED in result


def test_zero_hp_red() -> None:
    result = render_glyph("\u25c6", 0, 100)
    assert _RED in result


def test_custom_max_hp() -> None:
    # 120/150 = 80% -> bright white
    result = render_glyph("\u25c6", 120, 150)
    assert _BRIGHT_WHITE in result


def test_glyph_preserved() -> None:
    result = render_glyph("\u25c6", 50, 100)
    assert "\u25c6" in result


def test_reset_at_end() -> None:
    result = render_glyph("\u25c6", 50, 100)
    assert result.endswith(_RST)


# --- Stat-based background colors ---

_BG_RED = "\033[41m"
_BG_CYAN = "\033[46m"
_BG_BLUE = "\033[44m"
_BG_MAGENTA = "\033[45m"


def test_power_background() -> None:
    result = render_glyph("\u25c6", 100, 100, "power")
    assert _BG_RED in result


def test_speed_background() -> None:
    result = render_glyph("\u25c6", 100, 100, "speed")
    assert _BG_CYAN in result


def test_armor_background() -> None:
    result = render_glyph("\u25c6", 100, 100, "armor")
    assert _BG_BLUE in result


def test_mind_background() -> None:
    result = render_glyph("\u25c6", 100, 100, "mind")
    assert _BG_MAGENTA in result


def test_no_background_when_none() -> None:
    result = render_glyph("\u25c6", 100, 100, None)
    assert _BG_RED not in result
    assert _BG_CYAN not in result
    assert _BG_BLUE not in result
    assert _BG_MAGENTA not in result


def test_get_primary_stat_power() -> None:
    assert get_primary_stat(40, 20, 20, 20) == "power"


def test_get_primary_stat_balanced() -> None:
    assert get_primary_stat(25, 25, 25, 25) is None


def test_get_primary_stat_highest_wins() -> None:
    assert get_primary_stat(40, 35, 15, 10) == "power"
