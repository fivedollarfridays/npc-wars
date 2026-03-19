"""Tests for engine/glyphs.py — BOT_GLYPH format and glyph registry."""


from tests.conftest import make_bot


# --- Registry tests ---

def test_approved_glyphs_not_empty():
    from engine.glyphs import APPROVED_GLYPHS
    assert len(APPROVED_GLYPHS) >= 30


def test_default_glyph_in_approved():
    from engine.glyphs import APPROVED_GLYPHS, DEFAULT_GLYPH
    assert DEFAULT_GLYPH in APPROVED_GLYPHS


# --- validate_glyph tests ---

def test_validate_approved_glyph():
    from engine.glyphs import validate_glyph
    assert validate_glyph("\u25c6") == "\u25c6"  # ◆


def test_validate_emoji_accepted():
    """Emoji fallback from BOT_EMOJI should pass through."""
    from engine.glyphs import validate_glyph
    assert validate_glyph("\U0001f916") == "\U0001f916"  # 🤖


def test_validate_invalid_returns_default():
    from engine.glyphs import DEFAULT_GLYPH, validate_glyph
    assert validate_glyph("abc") == DEFAULT_GLYPH


def test_validate_empty_returns_default():
    from engine.glyphs import DEFAULT_GLYPH, validate_glyph
    assert validate_glyph("") == DEFAULT_GLYPH


def test_is_valid_glyph_true():
    from engine.glyphs import is_valid_glyph
    assert is_valid_glyph("\u25c6") is True


def test_is_valid_glyph_false():
    from engine.glyphs import is_valid_glyph
    assert is_valid_glyph("abc") is False


# --- Bot class integration ---

def test_bot_has_glyph_field():
    bot = make_bot(glyph="\u25c6")
    assert bot.glyph == "\u25c6"


def test_bot_glyph_defaults_to_emoji():
    bot = make_bot(emoji="\U0001f916")
    assert bot.glyph == "\U0001f916"


def test_self_dict_has_glyph():
    bot = make_bot(glyph="\u25c6")
    d = bot.to_self_dict()
    assert "glyph" in d
    assert d["glyph"] == "\u25c6"


def test_enemy_dict_has_glyph():
    bot = make_bot(glyph="\u25c6")
    d = bot.to_enemy_dict()
    assert "glyph" in d
    assert d["glyph"] == "\u25c6"


# --- Loader integration ---

def test_loader_reads_glyph(tmp_path):
    """Bot file with BOT_GLYPH loads with correct glyph in config."""
    from engine.loader import _load_single_bot

    bot_file = tmp_path / "test_glyph_bot.py"
    bot_file.write_text(
        'BOT_NAME = "GlyphBot"\n'
        'BOT_EMOJI = "\U0001f916"\n'
        'BOT_GLYPH = "\u25c6"\n'
        'def decide(state):\n'
        '    return ("rest",)\n'
    )
    config = _load_single_bot(str(bot_file), bot_file.name)
    assert config is not None
    assert config["glyph"] == "\u25c6"


def test_loader_falls_back_to_emoji(tmp_path):
    """Bot without BOT_GLYPH uses BOT_EMOJI as glyph."""
    from engine.loader import _load_single_bot

    bot_file = tmp_path / "test_emoji_bot.py"
    bot_file.write_text(
        'BOT_NAME = "EmojiBot"\n'
        'BOT_EMOJI = "\U0001f916"\n'
        'def decide(state):\n'
        '    return ("rest",)\n'
    )
    config = _load_single_bot(str(bot_file), bot_file.name)
    assert config is not None
    assert config["glyph"] == "\U0001f916"
