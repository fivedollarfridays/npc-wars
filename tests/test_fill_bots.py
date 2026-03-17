"""Tests for server.fill_bots — adaptive AI fill bot generation."""

from __future__ import annotations

from server.fill_bots import AI_EMOJI_POOL, generate_fill_bots


# --- Cycle 1: basic generation ---


def test_generate_single_bot():
    """Returns a list of 1 valid bot config."""
    bots = generate_fill_bots(1)
    assert isinstance(bots, list)
    assert len(bots) == 1


def test_generate_multiple_bots():
    """Returns correct number of bots."""
    bots = generate_fill_bots(3)
    assert len(bots) == 3


# --- Cycle 2: bot config structure ---


def test_bot_has_required_keys():
    """Each bot config must have name, emoji, bio, decide, source."""
    bots = generate_fill_bots(1)
    bot = bots[0]
    required = {"name", "emoji", "bio", "decide_func", "source"}
    assert required.issubset(bot.keys())


def test_decide_func_is_callable():
    """The decide_func must be callable."""
    bots = generate_fill_bots(1)
    assert callable(bots[0]["decide_func"])


# --- Cycle 3: emoji management ---


def test_distinct_emojis():
    """Multiple bots must have different emojis."""
    bots = generate_fill_bots(4)
    emojis = [b["emoji"] for b in bots]
    assert len(set(emojis)) == len(emojis)


def test_emojis_from_ai_pool():
    """All bot emojis must come from the AI emoji pool."""
    bots = generate_fill_bots(5)
    for bot in bots:
        assert bot["emoji"] in AI_EMOJI_POOL


def test_avoids_used_emojis():
    """Emojis already used by humans are excluded."""
    used = {AI_EMOJI_POOL[0], AI_EMOJI_POOL[1]}
    bots = generate_fill_bots(3, used_emojis=used)
    for bot in bots:
        assert bot["emoji"] not in used


# --- Cycle 4: skill level affects output ---


def test_skill_level_affects_params():
    """Different skill levels produce different bot source code."""
    low = generate_fill_bots(1, skill_level=0.2)
    high = generate_fill_bots(1, skill_level=0.9)
    # Different skill levels should produce different source (thresholds differ)
    assert low[0]["source"] != high[0]["source"]


# --- Cycle 5: run_match compatibility ---


def test_bot_compatible_with_run_match():
    """Fill bot configs work with run_match (smoke test)."""
    from engine.game import run_match

    bots = generate_fill_bots(4, skill_level=0.5)
    result = run_match(bots, match_id=999, seed=42)
    assert result["match_id"] == 999
    assert "rounds" in result
    assert len(result["rounds"]) > 0
