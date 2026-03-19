"""BOT_GLYPH registry and validation for NPC Wars visual identity."""

import logging

log = logging.getLogger(__name__)

# Approved single-character glyphs for bot identity
APPROVED_GLYPHS: frozenset[str] = frozenset({
    # Geometric
    "\u25c6", "\u25c7", "\u25cf", "\u25cb", "\u25a0", "\u25a1",  # ◆ ◇ ● ○ ■ □
    "\u25b2", "\u25b3", "\u25bc", "\u25bd", "\u2605", "\u2606",  # ▲ △ ▼ ▽ ★ ☆
    "\u25c8", "\u25c9", "\u25ca", "\u25d0", "\u25d1", "\u25d2",  # ◈ ◉ ◊ ◐ ◑ ◒
    "\u25d3", "\u25ef", "\u25a3", "\u25a4", "\u25a5", "\u25a6",  # ◓ ◯ ▣ ▤ ▥ ▦
    # Symbols
    "\u2694", "\u26a1", "\u2620", "\u2660", "\u2663", "\u2665",  # ⚔ ⚡ ☠ ♠ ♣ ♥
    "\u2666", "\u2b25", "\u2b21", "\u2b22", "\u2318", "\u2388",  # ♦ ⬥ ⬡ ⬢ ⌘ ⎈
    # Arrows
    "\u27a4", "\u2b9e", "\u27a2", "\u2b95",                      # ➤ ⮞ ➢ ⮕
    # Misc / chess / flags
    "\u2726", "\u2727", "\u2617", "\u2616", "\u2654", "\u2655",  # ✦ ✧ ☗ ☖ ♔ ♕
    "\u265a", "\u265b", "\u26ca", "\u2691", "\u2690", "\u2689",  # ♚ ♛ ⛊ ⚑ ⚐ ⚉
    "\u2688", "\u2687", "\u2686", "\u2685", "\u2684", "\u2683",  # ⚈ ⚇ ⚆ ⚅ ⚄ ⚃
    "\u2682", "\u2681", "\u2680",                                  # ⚂ ⚁ ⚀
})

DEFAULT_GLYPH: str = "\u25c6"  # ◆


def validate_glyph(glyph: str) -> str:
    """Validate a glyph string. Returns the glyph if valid, DEFAULT_GLYPH otherwise.

    A valid glyph is a single Unicode character (including multi-byte emoji)
    that is either in APPROVED_GLYPHS or a single grapheme (emoji fallback).
    Multi-character strings are rejected.
    """
    if not glyph:
        log.warning("Empty glyph, using default %s", DEFAULT_GLYPH)
        return DEFAULT_GLYPH

    # Check character count (len for str counts code points, but emoji
    # like 🤖 are single code points so len == 1 works)
    if len(glyph) != 1:
        log.warning("Invalid glyph %r (not single char), using default %s", glyph, DEFAULT_GLYPH)
        return DEFAULT_GLYPH

    # Approved set or any single character (emoji fallback)
    return glyph


def is_valid_glyph(glyph: str) -> bool:
    """Check if a glyph string is valid (single character)."""
    if not glyph or len(glyph) != 1:
        return False
    return True


__all__ = ["APPROVED_GLYPHS", "DEFAULT_GLYPH", "validate_glyph", "is_valid_glyph"]
