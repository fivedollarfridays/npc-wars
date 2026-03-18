"""Tests for combat visual FX: TankBot emoji change and defend event emission."""

from engine.combat import Bot, DEFEND_BONUS, STARTING_DEFENSE
from engine.rounds import resolve_defense


# --- Cycle 1: TankBot emoji ---


def test_tankbot_emoji_is_turtle():
    """TankBot uses turtle emoji, not shield (shield reserved for defend FX)."""
    from agentgrounds.wars.builtin_bots import example_tank

    assert example_tank.BOT_EMOJI == "\U0001f422"  # 🐢


def test_tankbot_legacy_emoji_is_turtle():
    """Legacy bots/ copy also uses turtle emoji."""
    from bots import example_tank

    assert example_tank.BOT_EMOJI == "\U0001f422"  # 🐢


# --- Cycle 2: defend event emission ---


def _make_bot(emoji: str = "X", x: int = 0, y: int = 0) -> Bot:
    return Bot(
        name="test", emoji=emoji, bio="", author="test",
        decide_func=lambda s: ("rest",), x=x, y=y,
    )


def test_resolve_defense_emits_defend_event():
    """resolve_defense returns a defend event when a bot defends."""
    bot = _make_bot(emoji="\U0001f422")
    actions = {"\U0001f422": ("defend",)}
    events = resolve_defense([bot], actions)
    assert isinstance(events, list)
    assert len(events) == 1
    assert events[0]["type"] == "defend"
    assert events[0]["emoji"] == "\U0001f422"


def test_resolve_defense_no_event_for_non_defenders():
    """resolve_defense returns no events for bots that don't defend."""
    bot = _make_bot(emoji="A")
    actions = {"A": ("attack", "north")}
    events = resolve_defense([bot], actions)
    assert events == []


def test_resolve_defense_still_sets_defense_bonus():
    """resolve_defense still applies DEFEND_BONUS on the bot object."""
    bot = _make_bot(emoji="D")
    actions = {"D": ("defend",)}
    resolve_defense([bot], actions)
    assert bot.defense == DEFEND_BONUS


def test_resolve_defense_resets_non_defenders():
    """Non-defending bots get STARTING_DEFENSE."""
    bot = _make_bot(emoji="R")
    bot.defense = 999
    actions = {"R": ("rest",)}
    resolve_defense([bot], actions)
    assert bot.defense == STARTING_DEFENSE


def test_resolve_defense_multiple_bots_mixed():
    """Multiple bots: only defenders produce events."""
    defender = _make_bot(emoji="D")
    attacker = _make_bot(emoji="A")
    rester = _make_bot(emoji="R")
    actions = {"D": ("defend",), "A": ("attack", "north"), "R": ("rest",)}
    events = resolve_defense([defender, attacker, rester], actions)
    assert len(events) == 1
    assert events[0]["emoji"] == "D"
