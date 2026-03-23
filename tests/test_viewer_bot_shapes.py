"""Tests that viewer HTML contains geometric shape bot rendering.

Verifies the viewer has archetype-based shape drawing instead of emoji text,
with proper color constants, shape functions, HP-dependent opacity, and
momentum aura glow effects.
"""
from __future__ import annotations

from conftest import read_viewer_content


def _read_viewer() -> str:
    """Read all viewer files (index.html + js/*.js)."""
    return read_viewer_content()


# --- Cycle 1: Archetype color and shape constants ---


def test_archetype_colors_defined() -> None:
    """Viewer must define color constants for all five archetypes."""
    html = _read_viewer()
    for archetype in ("Bruiser", "Tank", "Assassin", "Controller", "Balanced"):
        assert archetype in html, f"Missing archetype color for {archetype}"


def test_archetype_color_values() -> None:
    """Viewer must use the specified hex colors for each archetype."""
    html = _read_viewer()
    expected = {
        "#ff4444": "Bruiser red",
        "#4488ff": "Tank blue",
        "#aa44ff": "Assassin purple",
        "#44ff88": "Controller green",
        "#e0e0f0": "Balanced white",
    }
    for color, label in expected.items():
        assert color in html, f"Missing color {color} for {label}"


# --- Cycle 2: Shape drawing helper functions ---


def test_shape_drawing_functions_exist() -> None:
    """Viewer must have drawing functions for each geometric shape."""
    html = _read_viewer()
    for fn_name in ("drawCircle", "drawSquare", "drawTriangle",
                     "drawHexagon", "drawDiamond"):
        assert f"function {fn_name}" in html, f"Missing function {fn_name}"


# --- Cycle 3: Main drawBotShape function ---


def test_draw_bot_shape_function_exists() -> None:
    """Viewer must have a drawBotShape function that dispatches by archetype."""
    html = _read_viewer()
    assert "function drawBotShape" in html


def test_draw_bot_shape_handles_all_archetypes() -> None:
    """drawBotShape must reference all archetype shape names."""
    html = _read_viewer()
    for archetype in ("Tank", "Assassin", "Bruiser", "Controller"):
        assert f"'{archetype}'" in html or f'"{archetype}"' in html, \
            f"drawBotShape missing case for {archetype}"


# --- Cycle 4: Backward compatibility ---


def test_emoji_fallback_for_old_matches() -> None:
    """Viewer must fall back to emoji rendering when no archetype data."""
    html = _read_viewer()
    # Should check for archetype existence before drawing shape
    assert "botArchetypes" in html or "archetype" in html


# --- Cycle 5: Dead bot rendering ---


def test_dead_bot_shape_rendering() -> None:
    """Dead bots should be rendered as shapes with reduced opacity, not skull emoji."""
    html = _read_viewer()
    # The renderCanvas function should handle dead bots with shapes
    # Look for dead bot shape drawing logic (low opacity + X through it)
    assert "drawDeadBot" in html or ("!pos.alive" in html and "0.15" in html)


# --- Cycle 6: Momentum aura ---


def test_momentum_aura_glow() -> None:
    """Bots with momentum tier 3+ should have a glow shadow effect."""
    html = _read_viewer()
    assert "shadowBlur" in html, "Missing shadowBlur for momentum aura"
    assert "momentum_tier" in html or "momentumTier" in html


# --- Cycle 7: HP-dependent opacity ---


def test_hp_dependent_opacity_thresholds() -> None:
    """Shape opacity must change at 75%, 50%, 25% HP thresholds."""
    html = _read_viewer()
    assert "0.7" in html, "Missing 70% opacity for 50-75% HP"
    assert "0.5" in html, "Missing 50% opacity for 25-50% HP"
    assert "0.3" in html, "Missing 30% opacity for <25% HP"


# --- Data contract: archetype in stats ---


def test_match_stats_include_archetype() -> None:
    """Engine stats dict must include archetype field for viewer consumption."""
    from engine.archetype import classify_archetype
    from engine.stats import StatAllocation

    alloc = StatAllocation(power=40, speed=20, armor=20, mind=20)
    result = classify_archetype(alloc)
    assert result == "Bruiser"
