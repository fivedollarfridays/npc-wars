"""Tests for Watcher spectacle events — emitters, triggers, and effects."""

from engine.watcher_spectacle import (
    emit_sync_milestone_event,
    emit_watcher_kill_event,
    emit_watcher_spawn_event,
)
from engine.spectacle import DRAMA_WEIGHTS, TRIGGER_EFFECT_MAP, SpectacleEngine


# ---------- Event emitter tests ----------


def test_emit_watcher_spawn_event() -> None:
    evt = emit_watcher_spawn_event(x=5, y=3, sync=15.0)
    assert evt == {"type": "watcher_spawn", "x": 5, "y": 3, "sync": 15.0}


def test_emit_watcher_kill_event() -> None:
    evt = emit_watcher_kill_event(victim="\U0001f986", sync=73.0)
    assert evt == {"type": "watcher_kill", "victim": "\U0001f986", "sync": 73.0}


def test_emit_sync_milestone_event() -> None:
    evt = emit_sync_milestone_event(sync=50.0)
    assert evt == {"type": "watcher_sync", "sync": 50.0}


# ---------- SpectacleEngine trigger detection ----------

def _alive_bot(emoji: str, hp: int = 10) -> dict:
    return {"emoji": emoji, "alive": True, "hp": hp}


def test_score_round_detects_watcher_spawn_trigger() -> None:
    engine = SpectacleEngine()
    events = [{"type": "watcher_spawn", "sync": 15.0}]
    bots = [_alive_bot("A"), _alive_bot("B"), _alive_bot("C")]
    result = engine.score_round(events, bots)
    assert "watcher_spawn" in result.triggers


def test_score_round_detects_watcher_kill_trigger() -> None:
    engine = SpectacleEngine()
    events = [{"type": "watcher_kill", "victim": "\U0001f986", "sync": 73.0}]
    bots = [_alive_bot("A"), _alive_bot("B"), _alive_bot("C")]
    result = engine.score_round(events, bots)
    assert "watcher_kill" in result.triggers


def test_score_round_scores_watcher_sync_drama() -> None:
    engine = SpectacleEngine()
    events = [{"type": "watcher_sync", "sync": 50.0}]
    bots = [_alive_bot("A"), _alive_bot("B"), _alive_bot("C")]
    result = engine.score_round(events, bots)
    assert result.drama_score >= DRAMA_WEIGHTS["watcher_sync"]


def test_score_round_detects_watcher_sync_trigger() -> None:
    engine = SpectacleEngine()
    events = [{"type": "watcher_sync", "sync": 50.0}]
    bots = [_alive_bot("A"), _alive_bot("B"), _alive_bot("C")]
    result = engine.score_round(events, bots)
    assert "watcher_sync" in result.triggers


# ---------- Trigger-to-effect mapping ----------


def test_watcher_spawn_maps_to_dark_entrance() -> None:
    assert TRIGGER_EFFECT_MAP["watcher_spawn"] == "dark_entrance"


def test_watcher_kill_maps_to_skull_flash() -> None:
    assert TRIGGER_EFFECT_MAP["watcher_kill"] == "skull_flash"


def test_watcher_sync_maps_to_pulse_wave() -> None:
    assert TRIGGER_EFFECT_MAP["watcher_sync"] == "pulse_wave"
