"""Watcher spectacle event emitters for NPC Wars."""

from typing import Any

__all__ = [
    "emit_watcher_spawn_event",
    "emit_watcher_kill_event",
    "emit_sync_milestone_event",
]


def emit_watcher_spawn_event(x: int, y: int, sync: float) -> dict[str, Any]:
    """Emit a watcher spawn spectacle event with position and sync data."""
    return {"type": "watcher_spawn", "x": x, "y": y, "sync": sync}


def emit_watcher_kill_event(victim: str, sync: float) -> dict[str, Any]:
    """Emit a watcher kill spectacle event."""
    return {"type": "watcher_kill", "victim": victim, "sync": sync}


def emit_sync_milestone_event(sync: float) -> dict[str, Any]:
    """Emit a sync milestone spectacle event."""
    return {"type": "watcher_sync", "sync": sync}
