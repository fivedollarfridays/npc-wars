"""Tests for BOT_GLYPH on builtin bots."""

import os

from engine.bot_scanner import load_bot_module
from engine.loader import load_bots


BUILTIN_DIR = os.path.join(
    os.path.dirname(__file__), "..", "agentgrounds", "wars", "builtin_bots"
)


def _load_builtin(name: str):
    """Load a single builtin bot module by filename (without .py)."""
    path = os.path.join(BUILTIN_DIR, f"{name}.py")
    return load_bot_module(path, f"bot_{name}")


def test_aggro_has_glyph():
    mod = _load_builtin("example_aggro")
    assert hasattr(mod, "BOT_GLYPH")
    assert mod.BOT_GLYPH == "\u2694"  # ⚔


def test_tank_has_glyph():
    mod = _load_builtin("example_tank")
    assert hasattr(mod, "BOT_GLYPH")
    assert mod.BOT_GLYPH == "\u25a0"  # ■


def test_all_builtins_load_with_glyphs():
    """All non-template builtins produce configs with a 'glyph' key."""
    configs = load_bots(BUILTIN_DIR)
    assert len(configs) >= 5, f"Expected at least 5 bots, got {len(configs)}"
    for cfg in configs:
        assert "glyph" in cfg, f"{cfg['name']} missing glyph key"
        assert len(cfg["glyph"]) == 1, f"{cfg['name']} glyph not single char"


def test_template_uses_emoji_fallback():
    """Template bot has no BOT_GLYPH; glyph should equal the emoji."""
    mod = _load_builtin("template")
    assert not hasattr(mod, "BOT_GLYPH"), "template should NOT have BOT_GLYPH"
    # When loaded through loader, glyph falls back to emoji
    # Template is skipped by load_bots, so test module attrs directly
    emoji = mod.BOT_EMOJI
    from engine.glyphs import validate_glyph
    glyph = validate_glyph(emoji)
    assert glyph == emoji
