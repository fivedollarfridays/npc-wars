"""Tests for setup callback execution (T33.2)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from engine.callbacks import CallbackSet
from engine.combat import Bot


def _make_bot(
    name: str = "TestBot",
    emoji: str = "T",
    setup_fn: Any = None,
) -> Bot:
    """Create a minimal Bot with optional setup callback."""
    bot = Bot(
        name=name,
        emoji=emoji,
        bio="test",
        author="test",
        decide_func=lambda state: ("rest",),
        x=3,
        y=3,
    )
    bot.callbacks = CallbackSet(setup=setup_fn)
    return bot


# --- Cycle 1: setup called once, bots without setup unaffected ---


def test_setup_called_once_per_bot() -> None:
    """Setup callback is called exactly once for each bot that has one."""
    mock1 = MagicMock()
    mock2 = MagicMock()
    bots = [
        _make_bot(name="A", emoji="A", setup_fn=mock1),
        _make_bot(name="B", emoji="B", setup_fn=mock2),
    ]
    from engine.callback_runner import run_setup_callbacks

    run_setup_callbacks(bots, grid_size=10, storm_border=0)

    mock1.assert_called_once()
    mock2.assert_called_once()


def test_bot_without_setup_unaffected() -> None:
    """Bots without a setup callback are not touched."""
    mock_setup = MagicMock()
    bot_with = _make_bot(name="Has", emoji="H", setup_fn=mock_setup)
    bot_without = _make_bot(name="No", emoji="N", setup_fn=None)
    bots = [bot_with, bot_without]

    from engine.callback_runner import run_setup_callbacks

    run_setup_callbacks(bots, grid_size=10, storm_border=0)

    mock_setup.assert_called_once()
    # bot_without should still be in normal state
    assert bot_without.alive is True
    assert bot_without.hp > 0


# --- Cycle 2: state dict shape ---


def test_setup_receives_valid_state_dict() -> None:
    """Setup callback receives a dict with expected keys matching decide() shape."""
    captured: list[dict[str, Any]] = []

    def capture_setup(state: dict[str, Any]) -> None:
        captured.append(state)

    bots = [
        _make_bot(name="A", emoji="A", setup_fn=capture_setup),
        _make_bot(name="B", emoji="B", setup_fn=None),
    ]
    from engine.callback_runner import run_setup_callbacks

    run_setup_callbacks(bots, grid_size=10, storm_border=0)

    assert len(captured) == 1
    state = captured[0]
    # Must have top-level keys matching build_state shape
    assert "me" in state
    assert "enemies" in state
    assert "round" in state
    assert "grid_size" in state
    assert "storm_border" in state
    # round should be 0 (pre-match)
    assert state["round"] == 0
    assert state["grid_size"] == 10
    assert state["storm_border"] == 0
    # me should have bot self-dict fields
    assert "hp" in state["me"]
    assert "energy" in state["me"]
    assert "x" in state["me"]
    assert "y" in state["me"]


def test_setup_state_has_enemies() -> None:
    """Setup state dict includes enemy information."""
    captured: list[dict[str, Any]] = []

    def capture_setup(state: dict[str, Any]) -> None:
        captured.append(state)

    bots = [
        _make_bot(name="A", emoji="A", setup_fn=capture_setup),
        _make_bot(name="B", emoji="B", setup_fn=None),
        _make_bot(name="C", emoji="C", setup_fn=None),
    ]
    from engine.callback_runner import run_setup_callbacks

    run_setup_callbacks(bots, grid_size=10, storm_border=0)

    state = captured[0]
    enemies = state["enemies"]
    assert len(enemies) == 2
    enemy_names = {e["name"] for e in enemies}
    assert enemy_names == {"B", "C"}


# --- Cycle 3: exception safety ---


def test_setup_exception_doesnt_crash() -> None:
    """A bot raising in setup() does not crash the match or affect other bots."""
    def exploding_setup(state: dict[str, Any]) -> None:
        raise RuntimeError("bot bug")

    ok_mock = MagicMock()
    bots = [
        _make_bot(name="Bad", emoji="X", setup_fn=exploding_setup),
        _make_bot(name="Good", emoji="G", setup_fn=ok_mock),
    ]
    from engine.callback_runner import run_setup_callbacks

    # Should not raise
    run_setup_callbacks(bots, grid_size=10, storm_border=0)

    # Good bot's setup still ran
    ok_mock.assert_called_once()
    # Bad bot is still alive (setup failure doesn't kill)
    assert bots[0].alive is True
