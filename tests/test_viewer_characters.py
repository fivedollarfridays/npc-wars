"""Tests for viewer character rendering upgrade (T44.2).

Verifies shapes.js has weapon indicators, color interpolation,
character preview, and renderer.js uses character descriptors from match JSON.
"""
from __future__ import annotations

from conftest import read_viewer_content


def _read_viewer() -> str:
    """Read all viewer files (index.html + js/*.js)."""
    return read_viewer_content()


# --- Cycle 1: interpolateColor helper ---


def test_interpolate_color_function_exists() -> None:
    """shapes.js must define an interpolateColor helper."""
    html = _read_viewer()
    assert "function interpolateColor" in html


def test_interpolate_color_parses_hex() -> None:
    """interpolateColor must parse hex color components (parseInt + slice)."""
    html = _read_viewer()
    assert "parseInt" in html
    assert "slice" in html


# --- Cycle 2: drawWeaponIndicator function ---


def test_draw_weapon_indicator_function_exists() -> None:
    """shapes.js must define drawWeaponIndicator."""
    html = _read_viewer()
    assert "function drawWeaponIndicator" in html


def test_weapon_indicator_cases() -> None:
    """drawWeaponIndicator must handle all weapon indicator types."""
    html = _read_viewer()
    for indicator in ("dot", "line", "long_line", "wedge", "arc", "circle"):
        assert f"'{indicator}'" in html or f'"{indicator}"' in html, \
            f"Missing weapon indicator case for {indicator}"


# --- Cycle 3: drawCharacterPreview function ---


def test_draw_character_preview_function_exists() -> None:
    """shapes.js must define drawCharacterPreview for profile pages."""
    html = _read_viewer()
    assert "function drawCharacterPreview" in html


# --- Cycle 4: drawBotShape accepts character descriptor ---


def test_draw_bot_shape_accepts_character_param() -> None:
    """drawBotShape must accept a character descriptor parameter."""
    html = _read_viewer()
    # The function signature should include 'character' parameter
    assert "character" in html


def test_draw_bot_shape_uses_character_color() -> None:
    """drawBotShape should use character.color when descriptor is available."""
    html = _read_viewer()
    assert "character.color" in html or "character?.color" in html


def test_draw_bot_shape_uses_border_thickness() -> None:
    """drawBotShape should use character.border_thickness for stroke width."""
    html = _read_viewer()
    assert "border_thickness" in html


def test_draw_bot_shape_calls_weapon_indicator() -> None:
    """drawBotShape should call drawWeaponIndicator when character has one."""
    html = _read_viewer()
    assert "weapon_indicator" in html
    assert "drawWeaponIndicator" in html


# --- Cycle 5: HP color gradient (interpolation) ---


def test_hp_color_gradient_uses_interpolation() -> None:
    """drawBotShape should interpolate color toward gray based on HP."""
    html = _read_viewer()
    assert "interpolateColor" in html
    # Should interpolate toward a dark gray
    assert "#333333" in html or "'#333'" in html


# --- Cycle 6: renderer.js character descriptor lookup ---


def test_renderer_builds_character_lookup() -> None:
    """renderer.js must build a character descriptor lookup from matchData."""
    html = _read_viewer()
    # Should reference matchData.players for character descriptors
    assert "character" in html
    # The renderer should look up character data for each bot
    assert "players" in html or "matchData.players" in html


def test_renderer_passes_character_to_draw_bot_shape() -> None:
    """renderCanvas must pass character descriptor to drawBotShape."""
    html = _read_viewer()
    # drawBotShape call should include character argument
    # The existing call is: drawBotShape(ctx, px, py, archetype, hpPct, radius)
    # Updated should be: drawBotShape(ctx, px, py, archetype, hpPct, radius, character)
    assert "drawBotShape(ctx, px, py, archetype, hpPct, radius, character" in html \
        or "drawBotShape(ctx, px, py, archetype, hpPct, radius, char" in html
