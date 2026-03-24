"""Tests for viewer cosmetic rendering (T46.3).

Verifies shapes.js applies cosmetic overrides (color_palette, weapon_skin,
glow_effect), effects.js handles death_effect cosmetics, renderer.js builds
cosmetics lookup, store.html exists, and backward compatibility is preserved.
"""
from __future__ import annotations

from pathlib import Path

from conftest import read_viewer_content

STATIC_DIR = Path(__file__).resolve().parent.parent / "server" / "static"


def _read_viewer() -> str:
    """Read all viewer files (index.html + js/*.js)."""
    return read_viewer_content()


# --- Cycle 1: color_palette and weapon_skin cosmetic overrides ---


def test_shapes_reads_cosmetics_from_character() -> None:
    """drawBotShape must read cosmetics from the character descriptor."""
    html = _read_viewer()
    assert "cosmetics" in html, "shapes.js must reference cosmetics"


def test_color_palette_override() -> None:
    """shapes.js must apply color_palette cosmetic to override base color."""
    html = _read_viewer()
    assert "color_palette" in html, "Missing color_palette cosmetic handling"


def test_weapon_skin_override() -> None:
    """shapes.js must apply weapon_skin cosmetic to override weapon color."""
    html = _read_viewer()
    assert "weapon_skin" in html, "Missing weapon_skin cosmetic handling"


# --- Cycle 2: glow_effect cosmetic override ---


def test_glow_effect_override() -> None:
    """drawMomentumAura must apply glow_effect cosmetic color."""
    html = _read_viewer()
    assert "glow_effect" in html, "Missing glow_effect cosmetic handling"


# --- Cycle 3: death_effect cosmetic in effects.js ---


def test_death_effect_cosmetic() -> None:
    """Death animation must support cosmetic death_effect color override."""
    html = _read_viewer()
    # Also check events.js directly in case read_viewer_content doesn't include it
    events_path = Path(__file__).resolve().parent.parent / "viewer" / "js" / "events.js"
    events_content = events_path.read_text() if events_path.exists() else ""
    combined = html + events_content
    assert "death_effect" in combined, "Missing death_effect cosmetic handling"


# --- Cycle 4: renderer.js cosmetics lookup ---


def test_renderer_builds_cosmetics_lookup() -> None:
    """renderer.js must extract cosmetics from matchData.players."""
    html = _read_viewer()
    assert "cosmetics" in html
    # Should specifically look for cosmetics in player data
    assert "p.cosmetics" in html or "player.cosmetics" in html, \
        "renderer.js must read cosmetics from player data"


def test_renderer_merges_cosmetics_into_character() -> None:
    """renderer.js must attach cosmetics to the character descriptor."""
    html = _read_viewer()
    # Character lookup should include cosmetics
    assert "character" in html and "cosmetics" in html


# --- Cycle 5: store.html page ---


def test_store_html_exists() -> None:
    """server/static/store.html must exist."""
    store = STATIC_DIR / "store.html"
    assert store.exists(), "Missing server/static/store.html"


def test_store_html_has_dark_theme() -> None:
    """Store page must use dark cyberpunk theme matching other pages."""
    store = STATIC_DIR / "store.html"
    content = store.read_text(encoding="utf-8")
    assert "--bg" in content or "#0a0a0f" in content, "Store missing dark theme"


def test_store_html_has_catalog_fetch() -> None:
    """Store page must fetch /api/store for catalog data."""
    store = STATIC_DIR / "store.html"
    content = store.read_text(encoding="utf-8")
    assert "/api/store" in content, "Store must fetch /api/store"


def test_store_html_has_buy_button() -> None:
    """Store page must have buy functionality."""
    store = STATIC_DIR / "store.html"
    content = store.read_text(encoding="utf-8")
    assert "buy" in content.lower() or "Buy" in content, "Store must have buy functionality"


def test_store_html_has_coin_balance() -> None:
    """Store page must display coin balance."""
    store = STATIC_DIR / "store.html"
    content = store.read_text(encoding="utf-8")
    assert "coin" in content.lower() or "balance" in content.lower(), \
        "Store must display coin balance"


# --- Cycle 6: backward compatibility ---


def test_no_cosmetics_default_rendering() -> None:
    """When cosmetics is null/undefined, default colors must be used."""
    html = _read_viewer()
    # Must check cosmetics existence before using
    assert "cosmetics &&" in html or "cosmetics ?" in html, \
        "Must guard cosmetics access with null check"
