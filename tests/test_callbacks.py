"""Tests for engine/callbacks.py — callback registry + bot discovery."""

import types
from unittest.mock import MagicMock

from engine.callbacks import CALLBACK_NAMES, CallbackSet, discover_callbacks, execute_callback


# ── Cycle 1: CallbackSet dataclass ──────────────────────────────────


class TestCallbackSet:
    def test_default_fields_are_none(self):
        cs = CallbackSet()
        assert cs.setup is None
        assert cs.on_kill is None
        assert cs.react is None

    def test_callback_names_constant(self):
        assert CALLBACK_NAMES == ("setup", "on_kill", "react", "power_up", "evolve")

    def test_callable_fields_accept_functions(self):
        fn = lambda: None  # noqa: E731
        cs = CallbackSet(setup=fn, on_kill=fn, react=fn)
        assert cs.setup is fn
        assert cs.on_kill is fn
        assert cs.react is fn


# ── Cycle 2: discover_callbacks finds functions ─────────────────────


def _make_module(**attrs: object) -> types.ModuleType:
    """Helper: create a fake module with given attributes."""
    mod = types.ModuleType("_fake_bot")
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


class TestDiscoverCallbacks:
    def test_finds_setup_when_unlocked(self):
        def setup(state):
            pass
        mod = _make_module(setup=setup)
        cs = discover_callbacks(mod, unlocked_callbacks={"setup"})
        assert cs.setup is setup

    def test_finds_on_kill_when_unlocked(self):
        def on_kill(state, victim_emoji):
            pass
        mod = _make_module(on_kill=on_kill)
        cs = discover_callbacks(mod, unlocked_callbacks={"on_kill"})
        assert cs.on_kill is on_kill

    def test_finds_react_when_unlocked(self):
        def react(state, events):
            pass
        mod = _make_module(react=react)
        cs = discover_callbacks(mod, unlocked_callbacks={"react"})
        assert cs.react is react

    def test_finds_all_callbacks(self):
        def setup(state): pass
        def on_kill(state, victim_emoji): pass
        def react(state, events): pass
        mod = _make_module(setup=setup, on_kill=on_kill, react=react)
        cs = discover_callbacks(mod, unlocked_callbacks={"setup", "on_kill", "react"})
        assert cs.setup is setup
        assert cs.on_kill is on_kill
        assert cs.react is react


# ── Cycle 3: gating by unlocked_callbacks ───────────────────────────


class TestCallbackGating:
    def test_setup_gated_when_not_unlocked(self):
        def setup(state): pass
        mod = _make_module(setup=setup)
        cs = discover_callbacks(mod, unlocked_callbacks=set())
        assert cs.setup is None

    def test_on_kill_gated_when_not_unlocked(self):
        def on_kill(state, victim_emoji): pass
        mod = _make_module(on_kill=on_kill)
        cs = discover_callbacks(mod, unlocked_callbacks={"setup"})
        assert cs.on_kill is None

    def test_partial_unlock(self):
        def setup(state): pass
        def on_kill(state, victim_emoji): pass
        def react(state, events): pass
        mod = _make_module(setup=setup, on_kill=on_kill, react=react)
        cs = discover_callbacks(mod, unlocked_callbacks={"on_kill"})
        assert cs.setup is None
        assert cs.on_kill is on_kill
        assert cs.react is None


# ── Cycle 4: edge cases ─────────────────────────────────────────────


class TestDiscoverEdgeCases:
    def test_empty_module_returns_empty_callbackset(self):
        mod = _make_module()
        cs = discover_callbacks(mod, unlocked_callbacks={"setup", "on_kill", "react"})
        assert cs.setup is None
        assert cs.on_kill is None
        assert cs.react is None

    def test_non_callable_attribute_skipped(self):
        mod = _make_module(setup="not a function")
        cs = discover_callbacks(mod, unlocked_callbacks={"setup"})
        assert cs.setup is None

    def test_extra_attributes_ignored(self):
        def decide(state): pass
        def setup(state): pass
        mod = _make_module(decide=decide, setup=setup, helper=42)
        cs = discover_callbacks(mod, unlocked_callbacks={"setup"})
        assert cs.setup is setup

    def test_empty_unlocked_set_returns_empty(self):
        def setup(state): pass
        def on_kill(state, v): pass
        mod = _make_module(setup=setup, on_kill=on_kill)
        cs = discover_callbacks(mod, unlocked_callbacks=set())
        assert cs.setup is None
        assert cs.on_kill is None


# ── Cycle 5: execute_callback ────────────────────────────────────────


class TestExecuteCallback:
    def test_calls_function_with_args(self):
        mock = MagicMock()
        execute_callback(mock, "arg1", "arg2")
        mock.assert_called_once_with("arg1", "arg2")

    def test_none_callback_is_noop(self):
        # Should not raise
        execute_callback(None, "arg1")

    def test_exception_caught_gracefully(self):
        def bad_callback(state):
            raise RuntimeError("bot bug")
        # Should not raise
        execute_callback(bad_callback, {})

    def test_returns_none_on_success(self):
        result = execute_callback(lambda: None)
        assert result is None

    def test_returns_none_on_error(self):
        def bad(): raise ValueError("oops")
        result = execute_callback(bad)
        assert result is None


# ── Cycle 6: Bot.callbacks field ─────────────────────────────────────


class TestBotCallbacksField:
    def test_bot_has_callbacks_field(self):
        from engine.combat import Bot
        bot = Bot(
            name="test", emoji="T", bio="test", author="tester",
            decide_func=lambda s: ("rest",), x=0, y=0,
        )
        assert isinstance(bot.callbacks, CallbackSet)
        assert bot.callbacks.setup is None
        assert bot.callbacks.on_kill is None
        assert bot.callbacks.react is None
