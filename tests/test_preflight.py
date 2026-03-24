"""Tests for engine.preflight — bot preflight execution check."""

from __future__ import annotations


# -- Cycle 1: build_sample_state returns valid dict --

def test_build_sample_state_has_required_keys() -> None:
    from engine.preflight import build_sample_state

    state = build_sample_state()
    assert "me" in state
    assert "enemies" in state
    assert "grid_size" in state
    assert "storm_border" in state
    assert "round" in state
    assert "bumps_last_round" in state


def test_build_sample_state_me_has_position_and_hp() -> None:
    from engine.preflight import build_sample_state

    state = build_sample_state()
    me = state["me"]
    assert isinstance(me["x"], int)
    assert isinstance(me["y"], int)
    assert isinstance(me["hp"], float)
    assert isinstance(me["energy"], int)
    assert "unlocked_actions" in me


def test_build_sample_state_enemies_non_empty() -> None:
    from engine.preflight import build_sample_state

    state = build_sample_state()
    assert len(state["enemies"]) >= 1
    enemy = state["enemies"][0]
    assert "x" in enemy
    assert "hp" in enemy
    assert "name" in enemy


# -- Cycle 2: run_preflight with valid and invalid bots --

_VALID_BOT = '''\
BOT_NAME = "TestBot"
BOT_EMOJI = "T"

def decide(state):
    return ("rest",)
'''

_CRASHING_BOT = '''\
BOT_NAME = "CrashBot"
BOT_EMOJI = "C"

def decide(state):
    raise RuntimeError("boom")
'''

_NONE_BOT = '''\
BOT_NAME = "NoneBot"
BOT_EMOJI = "N"

def decide(state):
    return None
'''

_NON_TUPLE_BOT = '''\
BOT_NAME = "StringBot"
BOT_EMOJI = "S"

def decide(state):
    return "rest"
'''

_UNLOCKED_BOT = '''\
BOT_NAME = "TrapBot"
BOT_EMOJI = "P"

def decide(state):
    return ("trap", 3, 3)
'''

_NO_DECIDE_BOT = '''\
BOT_NAME = "NoDecide"
BOT_EMOJI = "X"
'''

_IMPORT_OS_BOT = '''\
import os
BOT_NAME = "BadImport"
BOT_EMOJI = "B"

def decide(state):
    return ("rest",)
'''

_KEY_ERROR_BOT = '''\
BOT_NAME = "KeyBot"
BOT_EMOJI = "K"

def decide(state):
    x = state["nonexistent_key"]
    return ("rest",)
'''


def test_valid_bot_passes_preflight() -> None:
    from engine.preflight import run_preflight

    ok, msg = run_preflight(_VALID_BOT)
    assert ok is True
    assert msg == "OK"


def test_crashing_bot_fails() -> None:
    from engine.preflight import run_preflight

    ok, msg = run_preflight(_CRASHING_BOT)
    assert ok is False
    assert "crashed" in msg
    assert "RuntimeError" in msg


def test_none_return_fails() -> None:
    from engine.preflight import run_preflight

    ok, msg = run_preflight(_NONE_BOT)
    assert ok is False
    assert "None" in msg


def test_non_tuple_return_fails() -> None:
    from engine.preflight import run_preflight

    ok, msg = run_preflight(_NON_TUPLE_BOT)
    assert ok is False
    assert "invalid type" in msg


def test_unlocked_action_fails() -> None:
    from engine.preflight import run_preflight

    ok, msg = run_preflight(_UNLOCKED_BOT)
    assert ok is False
    assert "trap" in msg
    assert "unlocked" in msg


def test_no_decide_function_fails() -> None:
    from engine.preflight import run_preflight

    ok, msg = run_preflight(_NO_DECIDE_BOT)
    assert ok is False
    assert "decide" in msg


def test_security_blocked_bot_fails() -> None:
    from engine.preflight import run_preflight

    ok, msg = run_preflight(_IMPORT_OS_BOT)
    assert ok is False
    assert "Security scan failed" in msg


def test_valid_bot_with_move_passes() -> None:
    from engine.preflight import run_preflight

    source = '''\
BOT_NAME = "MoveBot"
BOT_EMOJI = "M"

def decide(state):
    return ("move", 1, 0)
'''
    ok, msg = run_preflight(source)
    assert ok is True
    assert msg == "OK"


def test_key_error_bot_fails() -> None:
    from engine.preflight import run_preflight

    ok, msg = run_preflight(_KEY_ERROR_BOT)
    assert ok is False
    assert "crashed" in msg
    assert "KeyError" in msg
