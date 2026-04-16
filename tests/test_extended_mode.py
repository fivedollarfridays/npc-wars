"""Tests for extended match mode (T18.6)."""

from __future__ import annotations


# --- Cycle 1: MatchMode dataclass and get_mode() ---

def test_standard_mode_constants() -> None:
    """Standard mode has 200 rounds, 100 HP, 1.0x storm."""
    from engine.match_modes import STANDARD

    assert STANDARD.name == "standard"
    assert STANDARD.max_rounds == 200
    assert STANDARD.starting_hp == 100
    assert STANDARD.storm_delay_multiplier == 1.0


def test_extended_mode_constants() -> None:
    """Extended mode has 400 rounds, 200 HP, 1.5x storm delay."""
    from engine.match_modes import EXTENDED

    assert EXTENDED.name == "extended"
    assert EXTENDED.max_rounds == 400
    assert EXTENDED.starting_hp == 200
    assert EXTENDED.storm_delay_multiplier == 1.5


def test_get_mode_returns_standard_by_default() -> None:
    """get_mode() with no args returns standard mode."""
    from engine.match_modes import STANDARD, get_mode

    assert get_mode() is STANDARD


def test_get_mode_returns_extended() -> None:
    """get_mode('extended') returns extended mode."""
    from engine.match_modes import EXTENDED, get_mode

    assert get_mode("extended") is EXTENDED


def test_get_mode_unknown_falls_back_to_standard() -> None:
    """Unknown mode name falls back to standard."""
    from engine.match_modes import STANDARD, get_mode

    assert get_mode("nonexistent") is STANDARD


def test_match_mode_is_frozen() -> None:
    """MatchMode instances are immutable."""
    import pytest

    from engine.match_modes import STANDARD

    with pytest.raises(AttributeError):
        STANDARD.max_rounds = 999  # type: ignore[misc]


# --- Cycle 2: run_match accepts match_mode, result includes it ---

def _dummy_decide(state: dict) -> tuple[str, ...]:
    return ("rest",)


def _make_bot_config(name: str, emoji: str) -> dict:
    return {
        "name": name, "emoji": emoji, "bio": "test",
        "author": "test", "decide_func": _dummy_decide,
    }


def test_run_match_accepts_match_mode_param() -> None:
    """run_match should accept a match_mode parameter without error."""
    from engine.game import run_match

    configs = [_make_bot_config("A", "A"), _make_bot_config("B", "B")]
    result = run_match(configs, match_id=1, seed=42, match_mode="standard")
    assert result["winner"] in {"A", "B", "none"}


def test_match_result_includes_mode_standard() -> None:
    """Match result dict includes match_mode key for standard."""
    from engine.game import run_match

    configs = [_make_bot_config("A", "A"), _make_bot_config("B", "B")]
    result = run_match(configs, match_id=1, seed=42, match_mode="standard")
    assert result["match_mode"] == "standard"


def test_match_result_includes_mode_extended() -> None:
    """Match result dict includes match_mode key for extended."""
    from engine.game import run_match

    configs = [_make_bot_config("A", "A"), _make_bot_config("B", "B")]
    result = run_match(configs, match_id=1, seed=42, match_mode="extended")
    assert result["match_mode"] == "extended"


def test_extended_mode_uses_higher_starting_hp() -> None:
    """In extended mode, bots start with 200 HP (verified via _prepare_match)."""
    from engine.game import _prepare_match
    from engine.match_modes import get_mode

    configs = [_make_bot_config("A", "A"), _make_bot_config("B", "B")]
    mode = get_mode("extended")
    bots, _players, _grid_size, _rng = _prepare_match(configs, seed=42, mode=mode)

    assert all(b.hp == 200 for b in bots), f"Expected 200 HP, got {[b.hp for b in bots]}"


# --- Cycle 3: Queue depth and lobby auto-selection ---

def test_queue_depth_empty() -> None:
    """queue_depth returns 0 for empty queue."""
    from conftest import NotInMemoryQueue
    from server.queue import queue_depth, set_backend

    backend = NotInMemoryQueue()
    set_backend(backend)
    assert queue_depth() == 0


def test_queue_depth_with_items() -> None:
    """queue_depth returns count of items in queue."""
    from conftest import NotInMemoryQueue
    from server.queue import queue_depth, set_backend

    backend = NotInMemoryQueue()
    set_backend(backend)
    backend.lpush("npcwars:match_queue", '{"test": 1}')
    backend.lpush("npcwars:match_queue", '{"test": 2}')
    assert queue_depth() == 2


def _make_serializable_config(name: str, emoji: str) -> dict:
    """Bot config without decide_func so it's JSON-serializable for lobby tests."""
    return {"name": name, "emoji": emoji, "bio": "test", "author": "test"}


def test_lobby_standard_mode_when_queue_shallow() -> None:
    """Lobby uses standard mode when queue depth <= 3."""
    import json
    from unittest.mock import patch

    from server.lobby import Lobby
    from conftest import NotInMemoryQueue
    from server.queue import set_backend

    backend = NotInMemoryQueue()
    set_backend(backend)

    with patch("server.lobby._get_fill_bots", return_value=[]):
        lobby = Lobby()
        lobby.join(_make_serializable_config("A", "A"))
        lobby.join(_make_serializable_config("B", "B"))
        lobby._trigger_match()

    raw = backend.brpop("npcwars:match_queue", timeout=0)
    assert raw is not None
    job = json.loads(raw[1])
    assert job.get("match_mode") == "standard"


def test_lobby_auto_selects_extended_when_queue_deep() -> None:
    """Lobby selects extended mode when queue depth > 3."""
    import json
    from unittest.mock import patch

    from server.lobby import Lobby
    from conftest import NotInMemoryQueue
    from server.queue import set_backend

    backend = NotInMemoryQueue()
    set_backend(backend)

    # Pre-fill queue with 4 items (depth > 3)
    for i in range(4):
        backend.lpush("npcwars:match_queue", json.dumps({"filler": i}))

    with patch("server.lobby._get_fill_bots", return_value=[]):
        lobby = Lobby()
        lobby.join(_make_serializable_config("A", "A"))
        lobby.join(_make_serializable_config("B", "B"))
        lobby._trigger_match()

    # Drain filler items
    for _ in range(4):
        backend.brpop("npcwars:match_queue", timeout=0)

    raw = backend.brpop("npcwars:match_queue", timeout=0)
    assert raw is not None
    job = json.loads(raw[1])
    assert job["match_mode"] == "extended"
