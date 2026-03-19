"""Tests for hit probability wiring into build_state."""

from __future__ import annotations

from engine.combat import Bot
from engine.state import build_state
from engine.stats import DEFAULT_ALLOCATION


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_bot(emoji: str, x: int = 0, y: int = 0) -> Bot:
    """Create a minimal bot for testing."""
    return Bot(
        name=f"Bot{emoji}",
        emoji=emoji,
        bio="test",
        author="test",
        decide_func=lambda state: {"action": "rest"},
        x=x, y=y,
        stat_allocation=DEFAULT_ALLOCATION,
    )


# ---------------------------------------------------------------------------
# State dict wiring tests
# ---------------------------------------------------------------------------


def test_state_dict_has_hit_chance_vs() -> None:
    """build_state includes hit_chance_vs in me dict."""
    bot = _make_bot("A")
    enemy = _make_bot("B", x=1)
    state = build_state(bot, [bot, enemy], round_num=1, grid_size=10, storm_border=0)
    assert "hit_chance_vs" in state["me"]


def test_hit_chance_vs_has_all_enemies() -> None:
    """Each alive enemy emoji appears in hit_chance_vs."""
    bot = _make_bot("A")
    e1 = _make_bot("B", x=1)
    e2 = _make_bot("C", x=2)
    dead = _make_bot("D", x=3)
    dead.alive = False

    all_bots = [bot, e1, e2, dead]
    state = build_state(bot, all_bots, round_num=1, grid_size=10, storm_border=0)

    hit_vs = state["me"]["hit_chance_vs"]
    assert "B" in hit_vs
    assert "C" in hit_vs
    assert "D" not in hit_vs  # dead bots excluded


def test_hit_chance_vs_structure() -> None:
    """Each entry has hit_chance, crit_chance, dodge_chance, expected_damage."""
    bot = _make_bot("A")
    enemy = _make_bot("B", x=1)
    state = build_state(bot, [bot, enemy], round_num=1, grid_size=10, storm_border=0)

    entry = state["me"]["hit_chance_vs"]["B"]
    expected_keys = {"hit_chance", "crit_chance", "dodge_chance", "expected_damage"}
    assert set(entry.keys()) == expected_keys
    # All values are floats
    for key in expected_keys:
        assert isinstance(entry[key], float), f"{key} should be float"
