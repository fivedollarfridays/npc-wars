"""Tests for react callback infrastructure (T33.3)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from engine.callbacks import CallbackSet
from engine.combat import Bot


def _make_bot(
    emoji: str = "A",
    x: int = 5,
    y: int = 5,
    alive: bool = True,
    react_fn: Any = None,
) -> Bot:
    """Create a minimal bot for testing."""
    bot = Bot(
        name=f"bot_{emoji}",
        emoji=emoji,
        bio="test",
        author="tester",
        decide_func=lambda s: ("rest",),
        x=x,
        y=y,
    )
    bot.alive = alive
    if react_fn is not None:
        bot.callbacks = CallbackSet(react=react_fn)
    return bot


# ── Cycle 1: _build_nearby_events proximity filtering ─────────────


class TestBuildNearbyEvents:
    def test_event_within_3_tiles_included(self):
        from engine.callback_runner import _build_nearby_events

        bot = _make_bot(emoji="A", x=5, y=5)
        other = _make_bot(emoji="B", x=6, y=5)
        events = [{"type": "hit", "attacker": "B", "target": "A", "damage": 25}]
        result = _build_nearby_events(bot, events, [bot, other])
        assert len(result) == 1
        assert result[0]["type"] == "hit"

    def test_event_beyond_3_tiles_excluded(self):
        from engine.callback_runner import _build_nearby_events

        bot = _make_bot(emoji="A", x=0, y=0)
        far_bot = _make_bot(emoji="B", x=10, y=10)
        events = [{"type": "hit", "attacker": "B", "target": "C", "damage": 25}]
        result = _build_nearby_events(bot, events, [bot, far_bot])
        assert len(result) == 0

    def test_event_at_exactly_3_tiles_included(self):
        from engine.callback_runner import _build_nearby_events

        bot = _make_bot(emoji="A", x=5, y=5)
        other = _make_bot(emoji="B", x=8, y=5)  # Manhattan distance = 3
        events = [{"type": "hit", "attacker": "B", "target": "X", "damage": 10}]
        result = _build_nearby_events(bot, events, [bot, other])
        assert len(result) == 1

    def test_event_at_4_tiles_excluded(self):
        from engine.callback_runner import _build_nearby_events

        bot = _make_bot(emoji="A", x=5, y=5)
        other = _make_bot(emoji="B", x=9, y=5)  # Manhattan distance = 4
        events = [{"type": "hit", "attacker": "B", "target": "X", "damage": 10}]
        result = _build_nearby_events(bot, events, [bot, other])
        assert len(result) == 0


# ── Cycle 2: run_react_callbacks invocation ─────────────────────


class TestRunReactCallbacks:
    def test_react_called_for_alive_bot_with_callback(self):
        from engine.callback_runner import run_react_callbacks

        mock_react = MagicMock()
        bot = _make_bot(emoji="A", x=5, y=5, react_fn=mock_react)
        run_react_callbacks([bot], [], grid_size=10, storm_border=0, round_num=1)
        mock_react.assert_called_once()

    def test_react_receives_state_and_events(self):
        from engine.callback_runner import run_react_callbacks

        captured: list[tuple[Any, ...]] = []

        def spy_react(state: dict[str, Any], events: list[dict[str, Any]]) -> None:
            captured.append((state, events))

        bot = _make_bot(emoji="A", x=5, y=5, react_fn=spy_react)
        run_react_callbacks([bot], [], grid_size=10, storm_border=2, round_num=3)
        assert len(captured) == 1
        state, events = captured[0]
        assert state["round"] == 3
        assert state["grid_size"] == 10
        assert state["storm_border"] == 2
        assert isinstance(events, list)

    def test_dead_bots_not_called(self):
        from engine.callback_runner import run_react_callbacks

        mock_react = MagicMock()
        bot = _make_bot(emoji="A", alive=False, react_fn=mock_react)
        run_react_callbacks([bot], [], grid_size=10, storm_border=0, round_num=1)
        mock_react.assert_not_called()

    def test_bots_without_react_unaffected(self):
        from engine.callback_runner import run_react_callbacks

        bot_no_react = _make_bot(emoji="A")
        bot_with_react = _make_bot(emoji="B", react_fn=MagicMock())
        # Should not raise
        run_react_callbacks(
            [bot_no_react, bot_with_react], [],
            grid_size=10, storm_border=0, round_num=1,
        )
        bot_with_react.callbacks.react.assert_called_once()  # type: ignore[union-attr]

    def test_exception_in_react_does_not_crash(self):
        from engine.callback_runner import run_react_callbacks

        def bad_react(state: Any, events: Any) -> None:
            raise RuntimeError("bot bug")

        bot = _make_bot(emoji="A", react_fn=bad_react)
        # Should not raise
        run_react_callbacks([bot], [], grid_size=10, storm_border=0, round_num=1)

    def test_react_called_every_round_for_alive_bots(self):
        from engine.callback_runner import run_react_callbacks

        mock_react = MagicMock()
        bot = _make_bot(emoji="A", react_fn=mock_react)
        for r in range(1, 4):
            run_react_callbacks([bot], [], grid_size=10, storm_border=0, round_num=r)
        assert mock_react.call_count == 3

    def test_state_contains_self_dict_fields(self):
        from engine.callback_runner import run_react_callbacks

        captured: list[dict[str, Any]] = []

        def spy(state: dict[str, Any], events: list[dict[str, Any]]) -> None:
            captured.append(state)

        bot = _make_bot(emoji="A", x=3, y=4, react_fn=spy)
        run_react_callbacks([bot], [], grid_size=10, storm_border=1, round_num=5)
        state = captured[0]
        # to_self_dict fields
        assert state["x"] == 3
        assert state["y"] == 4
        assert "hp" in state
        assert "energy" in state
        # Augmented fields
        assert state["round"] == 5
        assert "enemies" in state

    def test_nearby_events_filtered_for_each_bot(self):
        from engine.callback_runner import run_react_callbacks

        captured_a: list[list[dict[str, Any]]] = []
        captured_b: list[list[dict[str, Any]]] = []

        def react_a(state: Any, events: list[dict[str, Any]]) -> None:
            captured_a.append(events)

        def react_b(state: Any, events: list[dict[str, Any]]) -> None:
            captured_b.append(events)

        bot_a = _make_bot(emoji="A", x=0, y=0, react_fn=react_a)
        bot_b = _make_bot(emoji="B", x=9, y=9, react_fn=react_b)
        bot_c = _make_bot(emoji="C", x=1, y=0)  # Near A, far from B
        events = [{"type": "hit", "attacker": "C", "target": "A", "damage": 10}]
        run_react_callbacks(
            [bot_a, bot_b, bot_c], events,
            grid_size=10, storm_border=0, round_num=1,
        )
        # A is near C (distance 1), should see the event
        assert len(captured_a[0]) == 1
        # B is far from C (distance ~17), should NOT see the event
        assert len(captured_b[0]) == 0
